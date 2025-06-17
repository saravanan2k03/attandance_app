import copy
from datetime import date, datetime
from django.utils.timezone import now
from tokenize import TokenError
from django.db.models import *
from django.db.models.functions import *
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework import permissions
from attendanceapp import serializers as seri 
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from attendanceapp.models import *
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.dateparse import parse_datetime
# Create your views here.
def members(request):
    return HttpResponse("Hello world!")


User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    def post(self, request):
        serializer = seri.RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                "user": serializer.data,
                "tokens": tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = seri.LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            tokens = get_tokens_for_user(user)
            return Response({
                "user": {
                    "username": user.username,
                    "email": user.email
                },
                "tokens": tokens
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):              
    def post(self, request):
        serializer = seri.ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                # Simulate sending reset link
                reset_link = f"http://example.com/reset-password/{user.id}/"
                send_mail(
                    subject='Password Reset Request',
                    message=f'Click the link to reset your password: {reset_link}',
                    from_email='noreply@example.com',
                    recipient_list=[email],
                    fail_silently=False,
                )
                return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found with this email."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           

class ResetPasswordView(APIView):
    def post(self, request, user_id):
        serializer = seri.ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(id=user_id)
                user.password = make_password(serializer.validated_data['new_password'])
                user.save()
                return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "Invalid user ID."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


class AddOrUpdateEmployeeView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            data = request.data
            profile_pic = request.FILES.get("profile_pic")
            document = request.FILES.get("document")
            license_key = data.get("license_key")

            if not license_key:
                return Response({"error": "License key is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

            username = data.get("username")
            try:
                user = CustomUser.objects.get(username=username)
                is_update = True
            except CustomUser.DoesNotExist:
                user = CustomUser(username=username)
                is_update = False

            user.email = data.get("email", user.email)
            user.first_name = data.get("first_name", user.first_name)
            user.last_name = data.get("last_name", user.last_name)
            user.user_type = "employee"
            if data.get("password"):
                user.password = make_password(data.get("password"))
            user.save()

            # Foreign Keys
            department = Department.objects.get(id=data["department_id"], organization=organization)
            designation = Designation.objects.get(id=data["designation_id"], organization=organization)

            try:
                employee = Employees.objects.get(user=user)
            except Employees.DoesNotExist:
                employee = Employees(user=user)

            employee.full_name = f"{user.first_name} {user.last_name}"
            employee.department = department
            employee.designation = designation
            employee.date_of_birth = data.get("date_of_birth", employee.date_of_birth)
            employee.gender = data.get("gender", employee.gender)
            employee.nationality = data.get("nationality", employee.nationality)
            employee.iqama_number = data.get("iqama_number", employee.iqama_number)
            employee.mob_no = data.get("mob_no", employee.mob_no)
            employee.joining_date = data.get("joining_date", employee.joining_date)
            employee.work_status = data.get("work_status", True)
            employee.basic_salary = data.get("basic_salary", 0.0)
            employee.gosi_applicable = data.get("gosi_applicable", True)
            employee.filename = data.get("filename", employee.filename)

            # Handle profile_pic
            if profile_pic:
                employee.profile_pic = profile_pic
            elif data.get("profile_pic") in ["", None]:
                employee.profile_pic = None

            # Handle document
            if document:
                employee.file = document
            elif data.get("document") in ["", None]:
                employee.file = None

            employee.save()

            # Handle Leave Details
            leave_details = data.get("leave_details", [])
            for leave_entry in leave_details:
                leave_type_name = leave_entry.get("leave_type")
                leave_count = leave_entry.get("leave_count", 0)

                if not leave_type_name:
                    continue

                leave_type = LEAVETYPE.objects.get(leave_type=leave_type_name.upper())
                leave_detail_obj, _ = EmployeeLeaveDetails.objects.get_or_create(
                    employee_id=user,
                    employee_leave_type=leave_type
                )
                leave_detail_obj.leave_count = leave_count
                leave_detail_obj.save()

            msg = "updated" if is_update else "added"
            return Response({"message": f"Employee and leave details {msg} successfully"}, status=status.HTTP_200_OK)

        except Department.DoesNotExist:
            return Response({"error": "Department not found for the organization"}, status=status.HTTP_400_BAD_REQUEST)
        except Designation.DoesNotExist:
            return Response({"error": "Designation not found for the organization"}, status=status.HTTP_400_BAD_REQUEST)
        except LEAVETYPE.DoesNotExist as e:
            return Response({"error": f"Leave type not found: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

###########need to Work###################
class AddAttendanceRecordView(APIView):
    def post(self, request):
        try:
            data = request.data
            license_key = data.get("license_key")
            employee_id = data.get("employee_id")
            check_in_time_str = data.get("check_in_time")
            check_out_time_str = data.get("check_out_time")

            if not (license_key and employee_id and check_in_time_str and check_out_time_str):
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            # Get organization from license key
            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_400_BAD_REQUEST)

            # Get employee
            try:
                employee = Employees.objects.get(id=employee_id)
            except Employees.DoesNotExist:
                return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

            # Get config for employee's shift
            config = Configuration.objects.filter(
                organization_id=organization,
                workshift=employee.workshift
            ).first()
            if not config:
                return Response({"error": "Shift configuration not found"}, status=status.HTTP_404_NOT_FOUND)

            # Parse times
            today = date.today()
            check_in = datetime.strptime(check_in_time_str, "%H:%M:%S")
            check_out = datetime.strptime(check_out_time_str, "%H:%M:%S")

            # Calculate work hours
            work_duration = check_out - check_in
            work_hours = round(work_duration.total_seconds() / 3600, 2)

            present_one = "Absent"
            present_two = "Absent"
            is_overtime = False
            overtime_hours = 0.0

            # Check if today is a holiday
            is_today_holiday = leaveDaysOfThisYearWise.objects.filter(
                organization_id=organization,
                leave_date__date=today,
                is_active=True
            ).exists()

            if not is_today_holiday:
                # ---- Punch In logic ----
                if config.punch_in_start_time <= check_in.time() <= config.punch_in_end_time:
                    present_one = "Present"
                elif config.punch_in_start_late_time and config.punch_in_end_late_time:
                    if config.punch_in_start_late_time <= check_in.time() <= config.punch_in_end_late_time:
                        present_one = "Late"
                    elif check_in.time() > config.punch_in_end_late_time:
                        present_one = "Absent"

                # ---- Punch Out logic ----
                if config.punch_out_start_time <= check_out.time() <= config.punch_out_end_time:
                    present_two = "Present"
                elif check_out.time() < config.punch_out_start_time:
                    present_two = "Early"
                elif config.over_time_working_end_time:
                    punch_out_end_dt = datetime.combine(today, config.punch_out_end_time)
                    overtime_end_dt = datetime.combine(today, config.over_time_working_end_time)

                    if check_out > punch_out_end_dt and check_out <= overtime_end_dt:
                        present_two = "Present"
                        is_overtime = True
                        overtime_duration = check_out - punch_out_end_dt
                        overtime_hours = round(overtime_duration.total_seconds() / 3600, 2)
                    elif check_out > overtime_end_dt:
                        present_two = "Absent"
            else:
                # If today is a holiday, override statuses
                present_one = "Absent"
                present_two = "Absent"

            # ---- Create or Update Attendance ----
            try:
                attendance = AttendanceRecords.objects.get(
                    employee_id=employee,
                    date=today
                )
                # Update existing record
                attendance.check_out_time = check_out.time()
                attendance.present_two = present_two
                attendance.work_hours = work_hours
                attendance.overtime_hours = overtime_hours
                attendance.is_overtime = is_overtime
                attendance.save()
                message = "Attendance record updated successfully"
            except AttendanceRecords.DoesNotExist:
                # Create new record
                AttendanceRecords.objects.create(
                    employee_id=employee,
                    organization_id=organization,
                    date=today,
                    check_in_time=check_in.time(),
                    check_out_time=check_out.time(),
                    present_one=present_one,
                    present_two=present_two,
                    work_hours=work_hours,
                    overtime_hours=overtime_hours,
                    is_overtime=is_overtime
                )
                message = "Attendance record created successfully"

            return Response({"message": message}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class EmployeeListView(APIView):
    def get(self, request):
        license_key = request.GET.get("license_key")
        gender = request.GET.get("gender")
        department = request.GET.get("department")
        designation = request.GET.get("designation")
        work_shift = request.GET.get("work_shift")

        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization
        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

        # Base queryset: employees of the organization
        employees = Employees.objects.filter(organization_id=organization)

        # Optional filters
        if gender:
            employees = employees.filter(gender__iexact=gender)
        if department:
            employees = employees.filter(department__department_name__iexact=department)
        if designation:
            employees = employees.filter(designation__designation_name__iexact=designation)
        if work_shift:
            employees = employees.filter(workshift__iexact=work_shift)

        serializer = seri.EmployeesSerializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    
class EmployeeLeaveDetailsByUserId(APIView):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            leave_details = EmployeeLeaveDetails.objects.filter(employee_id=user)

            if not leave_details.exists():
                return Response({"message": "No leave records found for this employee."}, status=status.HTTP_404_NOT_FOUND)

            serialized_data = seri.EmployeeLeaveDetailsSerializer(leave_details, many=True)
            return Response(serialized_data.data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)



class FilterLeaveRequestsAPIView(APIView):
    def post(self, request):
        try:
            data = request.data

            license_key = data.get("license_key")
            employee_id = data.get("employee_id")      # Optional
            status_filter = data.get("status")         # Optional: Approved, Pending, Rejected
            start_date = data.get("start_date")        # Optional
            end_date = data.get("end_date")            # Optional

            if not license_key:
                return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

            # Base QuerySet: all leaves in the organization
            queryset = LeaveMangement.objects.filter(organization_id=organization)

            # Optional filters
            if employee_id:
                queryset = queryset.filter(employee_id__user__id=employee_id)

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d").date()
                    queryset = queryset.filter(start_date__gte=start)
                except ValueError:
                    return Response({"error": "Invalid start_date format (YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)

            if end_date:
                try:
                    end = datetime.strptime(end_date, "%Y-%m-%d").date()
                    queryset = queryset.filter(end_date__lte=end)
                except ValueError:
                    return Response({"error": "Invalid end_date format (YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)

            # Format result
            leave_list = []
            for leave in queryset.select_related("employee_id", "leave_type"):
                leave_list.append({
                    "id": leave.id,
                    "employee_name": leave.employee_id.full_name,
                    "leave_type": leave.leave_type.leave_type_name,
                    "start_date": leave.start_date.strftime("%Y-%m-%d"),
                    "end_date": leave.end_date.strftime("%Y-%m-%d"),
                    "leave_days": leave.leave_days,
                    "status": leave.status,
                    "remarks": leave.remarks
                })

            return Response({"leave_requests": leave_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        





class AddDeviceView(APIView):
    def post(self, request):
        serializer = seri.DeviceSettingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Device added successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ListDeviceView(APIView):
    def get(self, request):
        devices = DeviceSetting.objects.all().order_by('device_name')
        serializer = seri.DeviceSettingSerializer(devices, many=True)
        return Response({"devices": serializer.data}, status=status.HTTP_200_OK)
    
class UpdateDeviceView(APIView):
    def patch(self, request, pk):
        device = get_object_or_404(DeviceSetting, pk=pk)
        serializer = seri.DeviceSettingSerializer(device, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Device updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




class AddDepartmentView(APIView):
    def post(self, request):
        try:
            license_key = request.data.get("license_key")
            department_name = request.data.get("name")

            if not license_key or not department_name:
                return Response({"error": "License key and department name are required"}, status=400)

            try:
                license = License.objects.get(key=license_key)
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=400)

            department = Department.objects.create(
                name=department_name,
                organization=license.organization
            )

            return Response({"message": "Department added successfully", "id": department.id}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# ----------------- Update Department -----------------
class UpdateDepartmentView(APIView):
    def put(self, request, department_id):
        try:
            department_name = request.data.get("name")
            if not department_name:
                return Response({"error": "Department name is required"}, status=400)

            try:
                department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                return Response({"error": "Department not found"}, status=404)

            department.name = department_name
            department.save()

            return Response({"message": "Department updated successfully"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# ----------------- Add Designation -----------------
class AddDesignationView(APIView):
    def post(self, request):
        try:
            license_key = request.data.get("license_key")
            title = request.data.get("title")

            if not license_key or not title:
                return Response({"error": "License key and designation title are required"}, status=400)

            try:
                license = License.objects.get(key=license_key)
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=400)

            designation = Designation.objects.create(
                title=title,
                organization=license.organization
            )

            return Response({"message": "Designation added successfully", "id": designation.id}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# ----------------- Update Designation -----------------
class UpdateDesignationView(APIView):
    def put(self, request, designation_id):
        try:
            title = request.data.get("title")
            if not title:
                return Response({"error": "Designation title is required"}, status=400)

            try:
                designation = Designation.objects.get(id=designation_id)
            except Designation.DoesNotExist:
                return Response({"error": "Designation not found"}, status=404)

            designation.title = title
            designation.save()

            return Response({"message": "Designation updated successfully"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        




class AddOrganizationView(APIView):
    def post(self, request):
        try:
            data = request.data
            user_id = data.get("created_by")  # ID of the CustomUser
            organization_name = data.get("organization_name")
            organization_address = data.get("organization_address")
            organization_details = data.get("organization_details")

            if not all([user_id, organization_name]):
                return Response({"error": "Required fields missing"}, status=status.HTTP_400_BAD_REQUEST)

            user = get_object_or_404(CustomUser, id=user_id)

            organization = Organization.objects.create(
                organization_name=organization_name,
                organization_address=organization_address,
                organization_details=organization_details,
                created_by=user
            )

            return Response({"message": "Organization created successfully", "organization_id": organization.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateOrganizationView(APIView):
    def put(self, request, org_id):
        try:
            organization = get_object_or_404(Organization, id=org_id)
            data = request.data

            organization.organization_name = data.get("organization_name", organization.organization_name)
            organization.organization_address = data.get("organization_address", organization.organization_address)
            organization.organization_details = data.get("organization_details", organization.organization_details)
            organization.is_active = data.get("is_active", organization.is_active)

            organization.save()

            return Response({"message": "Organization updated successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class HRDashboardView(APIView):
    def post(self, request):
        try:
            license_key = request.data.get("license_key")
            if not license_key:
                return Response({"error": "License key is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_400_BAD_REQUEST)

            today = datetime.today().date()
            current_month = today.month
            current_year = today.year

            # 1. Total employees
            total_employees = Employees.objects.filter(organization_id=organization).count()

            # 2. Attendance Records for Today
            todays_attendance = AttendanceRecords.objects.filter(
                organization_id=organization, date=today
            )

            # 3. Present today (either present_one or present_two is Present or Late)
            present_today = todays_attendance.filter(
                Q(present_one__in=["Present", "Late"]) | Q(present_two__in=["Present", "Late"])
            ).count()

            # 4. Absent today (both present_one and present_two are Absent)
            absent_today = todays_attendance.filter(
                present_one="Absent", present_two="Absent"
            ).count()

            # 5. Employees on leave today
            on_leave_today = LeaveMangement.objects.filter(
                organization_id=organization,
                start_date__lte=today,
                end_date__gte=today,
                status="Approved"
            )

            on_leave_count = on_leave_today.count()

            # 6. Pending leave requests
            pending_leave_requests = LeaveMangement.objects.filter(
                organization_id=organization,
                status="Pending"
            ).count()

            # 7. New Joins This Month
            new_joins = Employees.objects.filter(
                organization_id=organization,
                created_at__year=current_year,
                created_at__month=current_month
            ).count()

            # 8. Late Check-ins Today
            late_checkins = todays_attendance.filter(present_one="Late").count()

            # 9. Active Devices Today
            active_devices_today = DeviceSetting.objects.filter(
                organization_id=organization,
                last_activity__date=today
            ).count()

            # 10. Monthly Present/Absent Stats (last 6 months)
            last_6_months = AttendanceRecords.objects.filter(
                organization_id=organization
            ).annotate(month=TruncMonth("date")).values("month").annotate(
                present=Count("id", filter=Q(present_one__in=["Present", "Late"]) | Q(present_two__in=["Present", "Late"])),
                absent=Count("id", filter=Q(present_one="Absent", present_two="Absent"))
            ).order_by("-month")[:6]

            monthly_data = {
                "labels": [],
                "present": [],
                "absent": []
            }

            for item in reversed(last_6_months):
                month_name = item["month"].strftime("%b")
                monthly_data["labels"].append(month_name)
                monthly_data["present"].append(item["present"])
                monthly_data["absent"].append(item["absent"])

            # 11. Employees on leave today - List
            employee_leave_list = []
            for leave in on_leave_today:
                employee = leave.employee_id
                employee_leave_list.append({
                    "employee_id": employee.id,
                    "full_name": employee.full_name,
                    "department": employee.department.department_name if employee.department else "",
                    "designation": employee.designation.designation_name if employee.designation else "",
                    "leave_type": leave.leave_type.leave_type_name if leave.leave_type else "",
                    "leave_status": leave.status,
                    "leave_remarks": leave.remarks,
                    "leave_duration": f"{leave.start_date} to {leave.end_date}"
                })

            return Response({
                "summary": {
                    "total_employees": total_employees,
                    "present_today": present_today,
                    "absent_today": absent_today,
                    "on_leave_today": on_leave_count,
                    "pending_leave_requests": pending_leave_requests,
                    "new_joins_this_month": new_joins,
                    "late_checkins_today": late_checkins,
                    "active_devices_logged_in": active_devices_today
                },
                "employees_on_leave_today": employee_leave_list,
                "monthly_attendance_chart": monthly_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AddOrUpdateEmployeeLeaveDetailView(APIView):
    def post(self, request):
        try:
            data = request.data
            license_key = data.get("license_key")
            user_id = data.get("employee_id")  # CustomUser ID
            leave_type_id = data.get("leave_type_id")
            leave_count = int(data.get("leave_count", 0))
            leave_detail_id = data.get("leave_detail_id")  # optional

            if not all([license_key, user_id, leave_type_id]):
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate license key and get organization
            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate employee belongs to organization
            try:
                employee = Employees.objects.get(user__id=user_id, organization_id=organization)
            except Employees.DoesNotExist:
                return Response({"error": "Employee not found in organization"}, status=status.HTTP_404_NOT_FOUND)

            # Validate leave type
            try:
                leave_type = LEAVETYPE.objects.get(id=leave_type_id)
            except LEAVETYPE.DoesNotExist:
                return Response({"error": "Invalid leave type"}, status=status.HTTP_400_BAD_REQUEST)

            # If leave_detail_id is given -> Update
            if leave_detail_id:
                try:
                    leave_detail = EmployeeLeaveDetails.objects.get(id=leave_detail_id)
                    leave_detail.employee_id = employee.user
                    leave_detail.employee_leave_type = leave_type
                    leave_detail.leave_count = leave_count
                    leave_detail.save()
                    return Response({"message": "Leave detail updated"}, status=status.HTTP_200_OK)
                except EmployeeLeaveDetails.DoesNotExist:
                    return Response({"error": "Leave detail not found"}, status=status.HTTP_404_NOT_FOUND)

            # Else Create new
            leave_detail = EmployeeLeaveDetails.objects.create(
                employee_id=employee.user,
                employee_leave_type=leave_type,
                leave_count=leave_count
            )
            return Response({"message": "Leave detail created", "leave_detail_id": leave_detail.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class RequestLeaveAPIView(APIView):
    def post(self, request):
        try:
            data = request.data
            license_key = data.get("license_key")
            user_id = data.get("employee_id")
            leave_type_id = data.get("leave_type_id")
            start_date = data.get("start_date")  # format: YYYY-MM-DD
            end_date = data.get("end_date")
            remarks = data.get("remarks", "")

            if not all([license_key, user_id, leave_type_id, start_date, end_date]):
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate license and organization
            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_400_BAD_REQUEST)

            # Get employee and leave type
            try:
                employee = Employees.objects.get(user__id=user_id, organization_id=organization)
                leave_type = LEAVETYPE.objects.get(id=leave_type_id)
            except (Employees.DoesNotExist, LEAVETYPE.DoesNotExist):
                return Response({"error": "Employee or Leave Type not found"}, status=status.HTTP_404_NOT_FOUND)

            # Calculate leave days
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            leave_days = (end - start).days + 1
            if leave_days <= 0:
                return Response({"error": "End date must be after start date"}, status=status.HTTP_400_BAD_REQUEST)

            # Get employee's leave balance
            try:
                leave_detail = EmployeeLeaveDetails.objects.get(employee_id=employee.user, employee_leave_type=leave_type)
            except EmployeeLeaveDetails.DoesNotExist:
                return Response({"error": "Leave type not assigned to this employee"}, status=status.HTTP_404_NOT_FOUND)

            if leave_days > leave_detail.leave_count:
                return Response({
                    "error": "Insufficient leave balance",
                    "available": leave_detail.leave_count,
                    "requested": leave_days
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create leave request (status = Pending)
            LeaveMangement.objects.create(
                organization_id=organization,
                employee_id=employee,
                leave_type=leave_type,
                start_date=start,
                end_date=end,
                leave_days=leave_days,
                status="Pending",
                remarks=remarks
            )
            return Response({"message": "Leave request submitted successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



class ApproveOrRejectLeaveAPIView(APIView):
    def post(self, request):
        try:
            data = request.data
            leave_id = data.get("leave_id")
            action = data.get("action")  # "approve" or "reject"

            if not leave_id or action not in ["approve", "reject"]:
                return Response({"error": "Invalid leave ID or action"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                leave_request = LeaveMangement.objects.get(id=leave_id)
            except LeaveMangement.DoesNotExist:
                return Response({"error": "Leave request not found"}, status=status.HTTP_404_NOT_FOUND)

            if leave_request.status != "Pending":
                return Response({"error": f"Leave already {leave_request.status}"}, status=status.HTTP_400_BAD_REQUEST)

            if action == "approve":
                # Deduct leave count
                try:
                    leave_detail = EmployeeLeaveDetails.objects.get(
                        employee_id=leave_request.employee_id.user,
                        employee_leave_type=leave_request.leave_type
                    )
                    if leave_detail.leave_count < leave_request.leave_days:
                        return Response({"error": "Insufficient leave balance during approval"}, status=status.HTTP_400_BAD_REQUEST)

                    leave_detail.leave_count -= leave_request.leave_days
                    leave_detail.save()
                    leave_request.status = "Approved"
                    leave_request.save()
                    return Response({"message": "Leave approved"}, status=status.HTTP_200_OK)
                except EmployeeLeaveDetails.DoesNotExist:
                    return Response({"error": "Employee leave details not found"}, status=status.HTTP_404_NOT_FOUND)

            elif action == "reject":
                leave_request.status = "Rejected"
                leave_request.save()
                return Response({"message": "Leave rejected"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AddOrUpdateConfigurationView(APIView):
    def post(self, request):
        try:
            data = request.data
            license_key = data.get("license_key")
            workshift = data.get("workshift")

            if not license_key or not workshift:
                return Response({"error": "License key and workshift are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get organization from license key
            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

            # Check if Configuration exists
            config, created = Configuration.objects.get_or_create(
                organization_id=organization,
                workshift=workshift
            )

            # Update fields
            config.punch_in_start_time = data.get("punch_in_start_time", config.punch_in_start_time)
            config.punch_in_end_time = data.get("punch_in_end_time", config.punch_in_end_time)
            config.punch_in_start_late_time = data.get("punch_in_start_late_time", config.punch_in_start_late_time)
            config.punch_in_end_late_time = data.get("punch_in_end_late_time", config.punch_in_end_late_time)
            config.punch_out_start_time = data.get("punch_out_start_time", config.punch_out_start_time)
            config.punch_out_end_time = data.get("punch_out_end_time", config.punch_out_end_time)
            config.over_time_working_end_time = data.get("over_time_working_end_time", config.over_time_working_end_time)

            config.save()

            message = "Configuration created" if created else "Configuration updated"
            return Response({"message": message}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class AddOrUpdateHolidayView(APIView):
    def post(self, request):
        try:
            data = request.data
            license_key = data.get("license_key")
            leave_name = data.get("leave_name")
            leave_date = data.get("leave_date")  # ISO Format: "2025-12-25T00:00:00"
            leave_id = data.get("id")  # Optional for update
            created_by_id = data.get("created_by")  # Pass current user ID

            if not (license_key and leave_name and leave_date and created_by_id):
                return Response({"error": "Required fields: license_key, leave_name, leave_date, created_by"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate license
            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

            leave_date = parse_datetime(leave_date)
            if not leave_date:
                return Response({"error": "Invalid leave_date format. Use ISO format."}, status=status.HTTP_400_BAD_REQUEST)

            created_by = CustomUser.objects.get(id=created_by_id)

            if leave_id:
                # Update existing holiday
                try:
                    leave_obj = leaveDaysOfThisYearWise.objects.get(id=leave_id, organization_id=organization)
                except leaveDaysOfThisYearWise.DoesNotExist:
                    return Response({"error": "Leave day not found"}, status=status.HTTP_404_NOT_FOUND)

                leave_obj.leave_name = leave_name
                leave_obj.leave_date = leave_date
                leave_obj.is_active = data.get("is_active", leave_obj.is_active)
                leave_obj.save()
                return Response({"message": "Leave day updated successfully"}, status=status.HTTP_200_OK)

            else:
                # Add new holiday if not exists for the date
                existing = leaveDaysOfThisYearWise.objects.filter(
                    organization_id=organization,
                    leave_date__date=leave_date.date()
                ).first()

                if existing:
                    return Response({"error": "A leave already exists on this date"}, status=status.HTTP_400_BAD_REQUEST)

                leaveDaysOfThisYearWise.objects.create(
                    organization_id=organization,
                    leave_name=leave_name,
                    leave_date=leave_date,
                    created_by=created_by,
                    is_active=data.get("is_active", True)
                )

                return Response({"message": "Leave day added successfully"}, status=status.HTTP_201_CREATED)

        except CustomUser.DoesNotExist:
            return Response({"error": "Created by user not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ListHolidaysView(APIView):
    def get(self, request):
        license_key = request.GET.get("license_key")
        year = request.GET.get("year")
        month = request.GET.get("month")

        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization

            leaves = leaveDaysOfThisYearWise.objects.filter(
                organization_id=organization,
                is_active=True
            )

            if year:
                leaves = leaves.filter(leave_date__year=int(year))
            if month:
                leaves = leaves.filter(leave_date__month=int(month))

            results = [
                {
                    "id": leave.id,
                    "leave_name": leave.leave_name,
                    "leave_date": leave.leave_date.strftime("%Y-%m-%d"),
                    "is_active": leave.is_active
                }
                for leave in leaves
            ]

            return Response({"leaves": results}, status=status.HTTP_200_OK)

        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DeleteHolidayView(APIView):
    def delete(self, request, leave_id):
        license_key = request.GET.get("license_key")

        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization

            try:
                leave = leaveDaysOfThisYearWise.objects.get(id=leave_id, organization_id=organization)
                leave.is_active = False
                leave.save()
                return Response({"message": "Leave marked as inactive"}, status=status.HTTP_200_OK)

            except leaveDaysOfThisYearWise.DoesNotExist:
                return Response({"error": "Leave not found"}, status=status.HTTP_404_NOT_FOUND)

        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)