from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from attendanceapp import views

urlpatterns = [
    path('api/auth/register/', views.RegisterView.as_view(), name='register'),
    path('api/auth/login/', views.LoginView.as_view(), name='login'),
    path('api/auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('api/auth/reset-password/<int:user_id>/', views.ResetPasswordView.as_view(), name='reset_password'),
    path("reset-password/<int:user_id>/", views.ResetPasswordHTMLView.as_view(), name="reset-password-html"),
    # --- Employee Management ---
    path('api/employees/add-or-update/', views.AddOrUpdateEmployeeView.as_view(), name='add_or_update_employee'),
    path('api/employees/list/', views.EmployeeListView.as_view(), name='list_employees'),
    path('api/employees/leave-details/<int:user_id>/', views.EmployeeLeaveDetailsByUserId.as_view(), name='employee_leave_details'),
    path('api/employees/leave-details/add-or-update/', views.AddOrUpdateEmployeeLeaveDetailView.as_view(), name='add_update_employee_leave_detail'),
    # --- Attendance & Payroll ---
    path('api/attendance/add/', views.AddAttendanceRecordView.as_view(), name='add_attendance'),
    path('api/attendance/update/', views.UpdateAttendanceRecordView.as_view(), name='update-attendance'),
    path('api/payroll/generate/', views.GenerateOrUpdatePayrollView.as_view(), name='generate_payroll'),
    path('api/attendance/list/', views.AttendanceListView.as_view(), name='attendance-list'),

    # --- Leave Management ---
    path('api/leaves/request/', views.RequestLeaveAPIView.as_view(), name='request_leave'),
    path('api/leaves/filter/', views.FilterLeaveRequestsAPIView.as_view(), name='filter_leaves'),
    path('api/leaves/action/', views.ApproveOrRejectLeaveAPIView.as_view(), name='approve_or_reject_leave'),
    # --- Holiday Management ---
    path('api/holidays/list/', views.ListHolidaysView.as_view(), name='list_holidays'),
    path('api/holidays/add-or-update/', views.AddOrUpdateHolidayView.as_view(), name='add_or_update_holiday'),
    path('api/holidays/delete/<int:leave_id>/', views.DeleteHolidayView.as_view(), name='delete_holiday'),
    # --- Organization & Configuration ---
    path('api/organizations/add/', views.AddOrganizationView.as_view(), name='add_organization'),
    path('api/organizations/update/<int:org_id>/', views.UpdateOrganizationView.as_view(), name='update_organization'),

    path('api/departments/add/', views.AddDepartmentView.as_view(), name='add_department'),
    path('api/departments/update/<int:department_id>/', views.UpdateDepartmentView.as_view(), name='update_department'),
    
    path('api/designations/add/', views.AddDesignationView.as_view(), name='add_designation'),
    path('api/designations/update/<int:designation_id>/', views.UpdateDesignationView.as_view(), name='update_designation'),

    path('api/departments/', views.ListDepartmentsByLicenseView.as_view(), name='list_departments_by_license'),
    path('api/designations/', views.ListDesignationsByLicenseView.as_view(), name='list_designations_by_license'),

    path('api/config/add-or-update/', views.AddOrUpdateConfigurationView.as_view(), name='add_or_update_config'),
    path('api/configurations/', views.ListConfigurationByLicenseKeyView.as_view(), name='list-configurations-by-license'),


    path('api/leave-type/', views.AddOrUpdateLeaveTypeView.as_view(), name='add_or_update_leave_type'),
    path('api/leave-type/list/', views.ListLeaveTypesByLicenseView.as_view(), name='list-leave-types'),
    # --- Device Management ---
    path('api/devices/add/', views.AddDeviceView.as_view(), name='add_device'),
    path('api/devices/list/', views.ListDeviceByLicenseView.as_view(), name='list_devices'),
    path('api/devices/update/<int:pk>/', views.UpdateDeviceView.as_view(), name='update_device'),
    # --- HR Dashboard ---
    path('api/dashboard/hr/', views.HRDashboardView.as_view(), name='hr_dashboard'),
    path('api/attendance/dashboard/', views.EmployeeDashboardView.as_view(), name='attendance-dashboard'),
]
