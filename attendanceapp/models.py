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
    ("On Early","OnEarly"),
    ("On Leave","OnLeave"),

)

LEAVE_STATUS = (
    ("Pending","Pending"),
    ("Approved","Approved"),
    ("Rejected","Rejected"),
)

WORK_SHIFT_CHOICES = (
    ("Morning", "Morning"),
    ("Evening", "Evening"),
    ("Night", "Night"),
)



# Create your models here.
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, default='employee')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    

    def __str__(self):
        return self.username
    

class Organization(models.Model):
    organization_name=models.CharField(max_length=255,null=True,blank=True)
    organization_address=models.CharField(max_length=255,null=True,blank=True)
    organization_details=models.CharField(max_length=255,null=True,blank=True)
    created_by =models.ForeignKey(CustomUser,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_id_created_by")
    created_date=models.DateTimeField(auto_now=True, null=False, blank=False)
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = "organization"
        verbose_name = "organization detail"
        verbose_name_plural = "organizations details"
        
    def __str__(self):
        return self.organization_name
    
class Department(models.Model):
    organization_id =  models.ForeignKey(Organization,null=False, blank=False, on_delete=models.CASCADE, related_name="organization_department_id")
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
        return f"{self.department_name}"
    

class Designation(models.Model):
    organization_id =  models.ForeignKey(Organization,null=False, blank=False, on_delete=models.CASCADE, related_name="organization_designation_id")
    designation_name = models.CharField(max_length=255,null=False,blank=False)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    class Meta:
        db_table = "Designation"
        constraints = [
            models.UniqueConstraint(fields=["designation_name"], name="unique designation")
        ]
    def save(self, *args, **kwargs):
        # Convert the index_code value to uppercase before saving
        self.designation_name = self.designation_name.upper()
        super(Designation, self).save(*args, **kwargs)
    def __str__(self):
        return f"{self.designation_name}"

        
class Employees(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,null=False,blank=False,related_name="user_details")
    full_name = models.CharField(max_length=255,null=True,blank=True)
    finger_print_code = models.CharField(max_length=255,null=True,blank=True)
    department = models.ForeignKey(Department, null=False, blank=False, on_delete=models.CASCADE, related_name="department_id",)
    designation = models.ForeignKey(Designation, null=False, blank=False, on_delete=models.CASCADE, related_name="desination_id",)
    date_of_birth = models.DateField(null=False,blank=False)
    gender = models.CharField(max_length=8,choices=GENDER_CHOICE,null=True,blank=True)
    nationality = models.CharField(max_length=255,null=True,blank=True)
    iqama_number = models.CharField(max_length=255,null=True,blank=True)
    mob_no = models.CharField(max_length=16,null=True,blank=True)
    address = models.CharField(max_length=16,null=True,blank=True)
    joining_date = models.DateField(null=False,blank=False)
    work_status = models.BooleanField(default=True)	
    basic_salary = models.FloatField(default=0)
    gosi_applicable = models.BooleanField(default=True)
    gosi_deduction_amount = models.FloatField(blank=False,null=False,default=0)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/', blank=True, null=True)
    upload_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    created_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    workshift = models.CharField(max_length=20, choices=WORK_SHIFT_CHOICES, null=True, blank=True)
    organization = models.ForeignKey(Organization, null=False, blank=False, on_delete=models.CASCADE, related_name="employee_organization",)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    over_time_salary = models.FloatField(default=0)
    class Meta:
        db_table = "employee_details"
        verbose_name = "EmployeeDetail"
        verbose_name_plural = "EmployeeDetails"
        constraints = [
            models.UniqueConstraint(fields=["finger_print_code"], name="unique_Fingerprint")
        ]
        
    def __str__(self):
        return self.full_name

class LEAVETYPE(models.Model):
    organization_id =  models.ForeignKey(Organization,null=False, blank=False, on_delete=models.CASCADE, related_name="organization_leave_id")
    leave_type = models.CharField(max_length=255,null=False,blank=False)
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = "LEAVETYPE"
        constraints = [
            models.UniqueConstraint(fields=["leave_type"], name="unique leavetype")
        ]
    def save(self, *args, **kwargs):
        # Convert the index_code value to uppercase before saving
        self.leave_type = self.leave_type.upper()
        super(LEAVETYPE, self).save(*args, **kwargs)
    def __str__(self):
        return str(self.leave_type)
    

class EmployeeLeaveDetails(models.Model):
    employee_id = models.ForeignKey(CustomUser,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_id_leave_details")
    employee_leave_type = models.ForeignKey(LEAVETYPE,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_id_leavetype")
    leave_count = models.IntegerField(null=False, blank=False, default=0)
    class Meta:
        db_table = "EmployeeLeaveDetails"
        verbose_name = "Employee LeaveDetail"
        verbose_name_plural = "Employee LeaveDetails"
        constraints = [
            models.UniqueConstraint(fields=["employee_id", "employee_leave_type"], name="unique_employee_leave_type")
        ]
        
    def __str__(self):
        return f"{self.employee_id} - {self.employee_leave_type}"

class AttendanceRecords(models.Model):
    employee_id = models.ForeignKey(Employees,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_idss")
    organization_id =  models.ForeignKey(Organization,null=False, blank=False, on_delete=models.CASCADE, related_name="organization_attendance_id")
    date = models.DateField()
    check_in_time= models.TimeField(blank=True,null=True)
    present_one= models.CharField(max_length=255,choices=ATTENDANCE_STATUS,null=True,blank=True)
    present_two= models.CharField(max_length=255,choices=ATTENDANCE_STATUS,null=True,blank=True)
    check_out_time = models.TimeField(blank=True,null=True)
    work_hours = models.FloatField(default=0)
    is_overtime = models.BooleanField(default=False,blank=False,null=False)
    overtime_hours = models.FloatField(default=0)
    class Meta:
        db_table = "attendance_records"
        verbose_name = "AttendanceRecord"
        verbose_name_plural = "AttendanceRecords"
        
    def __str__(self):
        return self.employee_id.user.username
    

class PayrollRecords(models.Model):
    organization_id =  models.ForeignKey(Organization,null=False, blank=False, on_delete=models.CASCADE, related_name="organization_payroll_id")
    employee_id = models.ForeignKey(Employees,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_ids")
    month = models.DateField(blank=True,null=True)
    basic_salary = models.FloatField(default=0)
    total_days = models.IntegerField(null=False, blank=False, default=0)
    present_days = models.IntegerField(null=False, blank=False, default=0)
    absent_days = models.IntegerField(null=False, blank=False, default=0)
    allowance = models.FloatField(null=False, blank=False, default=0)
    deduction = models.FloatField(null=False, blank=False, default=0)
    net_salary = models.FloatField(null=False, blank=False, default=0)
    created_date = models.DateTimeField(auto_now=True, null=False, blank=False)
    total_overtime_hours =models.FloatField(null=False,blank=False,default=0)
    over_time_salary = models.FloatField(null=False,blank=False,default=0)
    total_working_hours = models.FloatField(null=False,blank=False,default=0)
    payroll_generated = models.BooleanField(default=False,blank=False,null=False)

    class Meta:
        db_table = "payroll_records"  
        verbose_name = "Payroll Record"
        verbose_name_plural = "payroll Records"
        
    def __str__(self):
        return self.employee_id.user.username
    

class LeaveMangement(models.Model):
    organization_id =  models.ForeignKey(Organization,null=False, blank=False, on_delete=models.CASCADE, related_name="organization_leavemanagement_id")
    employee_id = models.ForeignKey(Employees,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_id_leave")
    leave_type = models.ForeignKey(LEAVETYPE,null=False, blank=False, on_delete=models.CASCADE, related_name="employee_leave_type")
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
        return self.employee_id.user.username


class DeviceSetting(models.Model):
    organization_id =  models.ForeignKey(Organization,null=False, blank=False, on_delete=models.CASCADE, related_name="organization_devicesetting_id")
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
        return f"{self.device_name}"
    

class Configuration(models.Model):
    organization_id =  models.ForeignKey(Organization,null=False, blank=False, on_delete=models.CASCADE, related_name="organization_config_id")
    workshift = models.CharField(max_length=20, choices=WORK_SHIFT_CHOICES, null=True, blank=True)
    punch_in_start_time = models.TimeField(null=True,blank=True)
    punch_in_end_time  = models.TimeField(null=True,blank=True)
    punch_in_start_late_time = models.TimeField(null=True,blank=True)
    punch_in_end_late_time = models.TimeField(null=True,blank=True)
    punch_out_start_time = models.TimeField(null=True,blank=True)
    punch_out_end_time = models.TimeField(null=True,blank=True)
    over_time_working_end_time = models.TimeField(null=True,blank=True)
    class Meta:
        db_table = "configuration_management"
        verbose_name = "configuration Management"
        verbose_name_plural = "configuration Managements"
    def __str__(self):
        return f"{self.organization_id.organization_name}"
    
class License(models.Model):
    key = models.CharField(max_length=255, unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="licenses")
    
    def __str__(self):
        return self.key
    
class leaveDaysOfThisYearWise(models.Model):
    organization_id = models.ForeignKey(
        Organization,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="organization_leaveDays_id"
    )
    leave_name = models.CharField(max_length=255, null=False, blank=False)
    leave_date = models.DateField(null=False, blank=False)
    is_active = models.BooleanField(default=True)  # ✅ Only once
    added_date = models.DateTimeField(auto_now=True, blank=False, null=False)
    created_by = models.ForeignKey(
        CustomUser,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="employee_id_created_by_leaveDaysOfThisYearWise"
    )

    class Meta:
        db_table = "leaveDays_Of_This_Year_Wise"
        verbose_name = "leaveDays Of This Year Wise"
        verbose_name_plural = "leave Days Of This Year Wise"

    def __str__(self):
        return f"{self.leave_name} - {self.leave_date}"
