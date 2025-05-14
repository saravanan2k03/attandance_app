from django.contrib import admin

from attendanceapp.models import *

# Register your models here.
class EmployeesAdmim(admin.ModelAdmin):
    list_display = ("user","full_name",)


class DepartmentAdmim(admin.ModelAdmin):
    list_display = ("department_name","is_active","created_date")


class AttendanceRecordsAdmim(admin.ModelAdmin):
    list_display = ("employee_id","date","check_in_time","check_out_time","work_hours","overtime_hours","status")


class PayrollRecordsAdmin(admin.ModelAdmin):
    list_display = ("employee_id","month","basic_salary","total_days","present_days","absent_days","gosi_deduction","allowance","deduction","net_salary","created_date")


class LeaveMangementAdmin(admin.ModelAdmin):
    list_display = ("employee_id","leave_type","start_date","end_date","leave_days","status","remarks","created_date")

class DeviceSettingAdmin(admin.ModelAdmin):
    list_display = ("device_name","device_ip","device_port","sync_interval","last_sync_interval","is_active","created_date")





admin.site.register(Employees, EmployeesAdmim)
admin.site.register(Department, DepartmentAdmim)
admin.site.register(AttendanceRecords, AttendanceRecordsAdmim)
admin.site.register(PayrollRecords, PayrollRecordsAdmin)
admin.site.register(LeaveMangement, LeaveMangementAdmin)
admin.site.register(DeviceSetting, DeviceSettingAdmin)