from django.contrib import admin

from attendanceapp.models import *

# Register your models here.
class EmployeesAdmim(admin.ModelAdmin):
    list_display = ("user","full_name",)

class CustomUserAdmim(admin.ModelAdmin):
    list_display = ("last_name","first_name","email")


class DepartmentAdmim(admin.ModelAdmin):
    list_display = ("department_name","is_active","created_date")

class LEAVETYPEAdmim(admin.ModelAdmin):
    list_display = ("leave_type","is_active")

class DesignationAdmim(admin.ModelAdmin):
    list_display = ("designation_name","is_active","created_date")


class EmployeeLeaveDetailsAdmim(admin.ModelAdmin):
    list_display = ("employee_id","employee_leave_type","leave_count")


class AttendanceRecordsAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'date', 'check_in_time', 'check_out_time', 'present_one', 'present_two']  # REMOVE 'status'


class PayrollRecordsAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'month', 'net_salary', 'deduction']


class LeaveMangementAdmin(admin.ModelAdmin):
    list_display = ("employee_id","leave_type","start_date","end_date","leave_days","status","remarks","created_date")

class DeviceSettingAdmin(admin.ModelAdmin):
    list_display = ("device_name","device_ip","device_port","sync_interval","last_sync_interval","is_active","created_date")





admin.site.register(Employees, EmployeesAdmim)
admin.site.register(CustomUser, CustomUserAdmim)
admin.site.register(Department, DepartmentAdmim)
admin.site.register(LEAVETYPE, LEAVETYPEAdmim)
admin.site.register(Designation, DesignationAdmim)
admin.site.register(AttendanceRecords, AttendanceRecordsAdmin)
admin.site.register(PayrollRecords, PayrollRecordsAdmin)
admin.site.register(LeaveMangement, LeaveMangementAdmin)
admin.site.register(DeviceSetting, DeviceSettingAdmin)
admin.site.register(EmployeeLeaveDetails, EmployeeLeaveDetailsAdmim)