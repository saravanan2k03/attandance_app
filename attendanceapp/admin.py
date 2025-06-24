from django.contrib import admin
from attendanceapp.models import *


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("id","username", "first_name", "last_name", "email", "user_type")
    search_fields = ("username", "email")


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("organization_name", "organization_address", "created_by", "created_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("organization_name",)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("department_name", "organization_id", "is_active", "created_date")
    search_fields = ("department_name",)
    list_filter = ("organization_id",)


class DesignationAdmin(admin.ModelAdmin):
    list_display = ("designation_name", "organization_id", "is_active", "created_date")
    search_fields = ("designation_name",)
    list_filter = ("organization_id",)


class EmployeesAdmin(admin.ModelAdmin):
    list_display = ("id","user", "full_name", "department", "designation", "joining_date", "basic_salary", "workshift", "work_status")
    search_fields = ("full_name", "finger_print_code")
    list_filter = ("department", "designation", "workshift")


class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("id","leave_type", "organization_id", "is_active")


class EmployeeLeaveDetailsAdmin(admin.ModelAdmin):
    list_display = ("id","employee_id", "employee_leave_type", "leave_count")
    search_fields = ("employee_id__username",)


class AttendanceRecordsAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'date', 'check_in_time', 'check_out_time', 'present_one', 'present_two', 'work_hours', 'is_overtime']
    list_filter = ("date", "employee_id")
    search_fields = ("employee_id__user__username",)


class PayrollRecordsAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'month', 'basic_salary', 'net_salary', 'deduction', 'allowance', 'payroll_generated']
    list_filter = ("month", "payroll_generated")
    search_fields = ("employee_id__user__username",)


class LeaveMangementAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "leave_type", "start_date", "end_date", "leave_days", "status", "remarks", "created_date")
    list_filter = ("status", "leave_type")
    search_fields = ("employee_id__user__username",)


class DeviceSettingAdmin(admin.ModelAdmin):
    list_display = ("device_name", "device_ip", "device_port", "sync_interval", "last_sync_interval", "is_active", "created_date")
    search_fields = ("device_name", "device_ip")


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ("organization_id", "workshift", "punch_in_start_time", "punch_out_end_time")
    list_filter = ("organization_id", "workshift")


class LicenseAdmin(admin.ModelAdmin):
    list_display = ("key", "organization")
    search_fields = ("organization",)


class LeaveDaysOfThisYearWiseAdmin(admin.ModelAdmin):
    list_display = ("leave_name", "leave_date", "organization_id", "created_by", "is_active", "added_date")
    list_filter = ("leave_date", "is_active")


# Register all models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Designation, DesignationAdmin)
admin.site.register(Employees, EmployeesAdmin)
admin.site.register(LEAVETYPE, LeaveTypeAdmin)
admin.site.register(EmployeeLeaveDetails, EmployeeLeaveDetailsAdmin)
admin.site.register(AttendanceRecords, AttendanceRecordsAdmin)
admin.site.register(PayrollRecords, PayrollRecordsAdmin)
admin.site.register(LeaveMangement, LeaveMangementAdmin)
admin.site.register(DeviceSetting, DeviceSettingAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(leaveDaysOfThisYearWise, LeaveDaysOfThisYearWiseAdmin)
