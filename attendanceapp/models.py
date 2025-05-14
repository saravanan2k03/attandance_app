from django.db import models
from django.contrib.auth.models import AbstractUser

GENDER_CHOICE = (
    ("Male","Male"),
    ("Female","Female"),
    ("Other","Other")
)
ATTENDANCE_STATUS = (
    ("Present","Present"),
    ("Absent","Absent"),
    ("Late","Late"),
    ("On Leave","OnLeave"),
)
LEAVE_TYPE = (
    ("Sick","Sick"),
    ("Casual","Casual"),
    ("Emergency","Emergency"),
    ("Other","Other")
)
LEAVE_STATUS = (
    ("Pending","Pending"),
    ("Approved","Approved"),
    ("Rejected","Rejected"),
)
# Create your models here.
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, default='employee')
    

    def __str__(self):
        return self.email
    
class Department(models.Model):
    department_name=models.CharField(max_length=255,null=False,blank=False)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    class Meta:
        db_table = "Department"
        constraints = [
            models.UniqueConstraint(fields=["department_name"], name="unique depart")
        ]
    def save(self, *args, **kwargs):
        # Convert the index_code value to uppercase before saving
        self.department_name = self.department_name.upper()
        super(Department, self).save(*args, **kwargs)
    def __str__(self):
        return f"{self.department_name}: {self.is_active} "
    
class Employees(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,null=False,blank=False,related_name="user_details")
    full_name = models.CharField(max_length=255,null=True,blank=True)
    department = models.ForeignKey(Department, null=False, blank=False, on_delete=models.CASCADE, related_name="department_id",)
    designation = models.CharField(max_length=255,null=False,blank=False)
    date_of_birth = models.DateTimeField(null=False,blank=False)
    gender = models.CharField(max_length=8,choices=GENDER_CHOICE,null=True,blank=True)
    nationality = models.CharField(max_length=255,null=True,blank=True)
    iqama_number = models.CharField(max_length=255,null=True,blank=True)
    mob_no = models.CharField(max_length=16,null=True,blank=True)
    joining_date = models.DateTimeField(null=False,blank=False)
    work_status = models.BooleanField(default=True)	
    basic_salary = models.FloatField(default=0)
    gosi_applicable = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    class Meta:
        db_table = "employee_details"
        verbose_name = "EmployeeDetail"
        verbose_name_plural = "EmployeeDetails"
        
    def __str__(self):
        return self.user.username
 

class AttendanceRecords(models.Model):
    employee_id = models.ForeignKey(Employees,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_idss")
    date = models.DateField(auto_now=True)
    check_in_time= models.TimeField(blank=True,null=False)
    check_out_time = models.TimeField(blank=True,null=False)
    work_hours = models.FloatField(default=0)
    overtime_hours = models.FloatField(default=0)
    status = models.CharField(max_length=255,choices=ATTENDANCE_STATUS,null=True,blank=True)
    class Meta:
        db_table = "attendance_records"
        verbose_name = "AttendanceRecord"
        verbose_name_plural = "AttendanceRecords"
        
    def __str__(self):
        return self.employee_id.user.email
    

class PayrollRecords(models.Model):
    employee_id = models.ForeignKey(Employees,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_ids")
    month = models.CharField(max_length=255,null=True,blank=True)
    basic_salary = models.FloatField(default=0)
    total_days = models.IntegerField(null=False, blank=False, default=0)
    present_days = models.IntegerField(null=False, blank=False, default=0)
    absent_days = models.IntegerField(null=False, blank=False, default=0)
    gosi_deduction =models.FloatField(null=False, blank=False, default=0)
    allowance = models.FloatField(null=False, blank=False, default=0)
    deduction = models.FloatField(null=False, blank=False, default=0)
    net_salary = models.FloatField(null=False, blank=False, default=0)
    created_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    class Meta:
        db_table = "payroll_records"
        verbose_name = "Payroll Record"
        verbose_name_plural = "payroll Records"
        
    def __str__(self):
        return self.employee_id.user.email
    

class LeaveMangement(models.Model):
    employee_id = models.ForeignKey(Employees,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_id_leave")
    leave_type = models.CharField(max_length=255,choices=LEAVE_TYPE,null=True,blank=True)
    start_date = models.DateField(null=False,blank=False)
    end_date = models.DateField(null=False,blank=False)
    leave_days = models.IntegerField(null=False, blank=False, default=0)
    status = models.CharField(max_length=255,choices=LEAVE_STATUS,null=True,blank=True)
    remarks = models.TextField(null=True,blank=True)
    created_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    class Meta:
        db_table = "leave_management"
        verbose_name = "Leave Management"
        verbose_name_plural = "Leave Managements"
        
    def __str__(self):
        return self.employee_id.user.email


class DeviceSetting(models.Model):
    device_name = models.CharField(max_length=255,null=False,blank=False)
    device_ip = models.CharField(max_length=255,null=False,blank=False)
    device_port = models.CharField(max_length=255,null=False,blank=False)
    sync_interval = models.DateTimeField(null=True,blank=True)
    last_sync_interval = models.DateTimeField(null=True,blank=True)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    class Meta:
        db_table = "device_setting"
        constraints = [
            models.UniqueConstraint(fields=["device_name"], name="unique device")
        ]
    def save(self, *args, **kwargs):
        # Convert the index_code value to uppercase before saving
        self.device_name = self.device_name.upper()
        super(DeviceSetting, self).save(*args, **kwargs)
    def __str__(self):
        return f"{self.device_name}: {self.is_active}"
    



    
