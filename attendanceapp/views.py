import calendar
import copy
from datetime import date, datetime
from email.utils import parsedate
import json
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
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils.dateparse import parse_date 
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

                context = {
                "username":user.username,
                "email":email,
                "logo_url":f"http://example.com/static/admin/img/calendar-icons.svg",
                 "reset_link" : f"http://example.com/reset-password/{user.id}/"
                }
                html_content = render_to_string("email.html", context)

                email_message = EmailMessage(
                    subject='Password Reset Request',
                    body=html_content,
                    from_email='noreply@example.com',
                    to=['noreply@example.com'],
                    # cc=[cc_email]
                )

                email_message.content_subtype = "html"

                # Send email
                email_message.send()
                # send_mail(
                #     subject='Password Reset Request',
                #     message=f'Click the link to reset your password: {reset_link}',
                #     from_email='noreply@example.com',
                #     recipient_list=[email],
                #     fail_silently=False,
                # )
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

        
class ResetPasswordHTMLView(APIView):
    def get(self, request, user_id):
        return render(request, "reset_password.html", {"user_id": user_id})

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
        

class EmployeeDashboardView(APIView):
    def get(self, request):
        license_key = request.query_params.get("license_key")
        employee_id = request.query_params.get("employee_id")

        if not license_key or not employee_id:
            return Response({"error": "license_key and employee_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Get organization by license
            license_obj = License.objects.get(key=license_key)
            organization = license_obj.organization

            # 2. Get employee and ensure belongs to organization
            employee = Employees.objects.get(id=employee_id, organization=organization)

            # 3. Date range for current month
            today = now().date()
            first_day = today.replace(day=1)
            last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

            # 4. Attendance records for this employee this month
            records = AttendanceRecords.objects.filter(
                employee_id=employee,
                organization_id=organization,
                date__range=(first_day, last_day)
            )

            attendance_this_month = records.filter(present_one="Present", present_two="Present").count()
            leaves_taken = records.filter(present_one="Absent", present_two="Absent").count()
            late_logins = records.filter(Q(present_one="Late") | Q(present_two="Late")).count()
            absent_in_this_month = records.filter(Q(present_one="Absent") | Q(present_two="Absent")).count()
            overtime_hours = records.aggregate(total=Sum("overtime_hours"))["total"] or 0

            pending_leave_requests = LeaveMangement.objects.filter(
                employee_id=employee,
                organization_id=organization,
                status="Pending"
            ).count()

            # Today's punch in/out
            today_record = records.filter(date=today).first()
            punch_in = today_record.check_in_time.strftime('%I:%M %p') if today_record and today_record.check_in_time else "00:00"
            punch_out = today_record.check_out_time.strftime('%I:%M %p') if today_record and today_record.check_out_time else "00:00"

            # Table data
            table_data = [
                {
                    "date": r.date.strftime('%Y-%m-%d'),
                    "punch_in": r.check_in_time.strftime('%I:%M %p') if r.check_in_time else "00:00",
                    "punch_out": r.check_out_time.strftime('%I:%M %p') if r.check_out_time else "00:00"
                }
                for r in records.order_by("date")
            ]

            total_days = records.count()
            pie_chart = {
                "present": round((attendance_this_month / total_days) * 100, 2) if total_days else 0,
                "absent": round((absent_in_this_month / total_days) * 100, 2) if total_days else 0,
                "leave": round((leaves_taken / total_days) * 100, 2) if total_days else 0
            }

            return Response({
                "employee_name": employee.full_name,
                "attendance_this_month": attendance_this_month,
                "leaves_taken": leaves_taken,
                "late_logins": late_logins,
                "absent_in_this_month": absent_in_this_month,
                "overtime_working": overtime_hours,
                "pending_leave_requests": pending_leave_requests,
                "punch_in": punch_in,
                "punch_out": punch_out,
                "table_data": table_data,
                "pie_chart": pie_chart
            }, status=status.HTTP_200_OK)

        except License.DoesNotExist:
            return Response({"error": "Invalid license key."}, status=status.HTTP_404_NOT_FOUND)
        except Employees.DoesNotExist:
            return Response({"error": "Employee not found under this organization."}, status=status.HTTP_404_NOT_FOUND)



class AddOrUpdateEmployeeView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            profile_pic = request.FILES.get("profile_pic", None)
            document = request.FILES.get("document", None)
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
            department = Department.objects.get(id=data["department_id"], organization_id=organization.id)
            designation = Designation.objects.get(id=data["designation_id"], organization_id=organization.id)

            try:
                employee = Employees.objects.get(user=user)
            except Employees.DoesNotExist:
                employee = Employees(user=user)

            employee.full_name = f"{user.first_name} {user.last_name}"
            employee.department = department
            employee.designation = designation
            employee.date_of_birth = data.get("date_of_birth")
            employee.gender = data.get("gender", employee.gender)
            employee.nationality = data.get("nationality", employee.nationality)
            employee.iqama_number = data.get("iqama_number", employee.iqama_number)
            employee.mob_no = data.get("mob_no", employee.mob_no)
            employee.joining_date = data.get("joining_date")
            employee.work_status = data.get("work_status", True)
            employee.basic_salary = data.get("basic_salary", 0.0)
            employee.gosi_applicable = data.get("gosi_applicable", True)
            employee.filename = data.get("filename", employee.filename)
            employee.organization = organization

            if profile_pic:
                employee.profile_pic = profile_pic

            if document:
                employee.file = document

            employee.save()

            # Handle Leave Details
            leave_details = data.get("leave_details", [])
            if isinstance(leave_details, str):
                leave_details = json.loads(leave_details)

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

            # Return leave details (if any)
            leave_data = []
            leave_objs = EmployeeLeaveDetails.objects.filter(employee_id=user)
            for leave in leave_objs:
                leave_data.append({
                    "leave_type": leave.employee_leave_type.leave_type,
                    "leave_count": leave.leave_count
                })

            msg = "updated" if is_update else "added"
            return Response({
                "message": f"Employee and leave details {msg} successfully",
                # "leave_details": leave_data
            }, status=status.HTTP_200_OK)

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
            punch_time_str = data.get("time")  # renamed from check_in_time/check_out_time
            if not (license_key and employee_id and punch_time_str):
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

            # Get config
            config = Configuration.objects.filter(
                organization_id=organization,
                workshift=employee.workshift
            ).first()
            if not config:
                return Response({"error": "Shift configuration not found"}, status=status.HTTP_404_NOT_FOUND)

            # Parse time
            today = date.today()
            punch_time = datetime.strptime(punch_time_str, "%H:%M:%S")

            # Determine whether it's a check-in or check-out
            if config.punch_in_start_time <= punch_time.time() <= config.punch_in_end_time:
                is_check_in = True
            elif config.punch_out_start_time and punch_time.time() <= config.punch_out_start_time:
                is_check_in = False
            else:
                # Determine default fallback (e.g., based on whether check-in already exists)
                existing = AttendanceRecords.objects.filter(employee_id=employee, date=today).first()
                is_check_in = not existing or not existing.check_in_time

            # ---- Create or update logic ----
            attendance, created = AttendanceRecords.objects.get_or_create(
                employee_id=employee,
                organization_id=organization,
                date=today,
                defaults={
                    "check_in_time": None,
                    "check_out_time": None,
                    "present_one": "Absent",
                    "present_two": "Absent",
                    "work_hours": 0,
                    "overtime_hours": 0,
                    "is_overtime": False,
                }
            )

            message = "Attendance record updated"

            # Check holiday
            is_today_holiday = leaveDaysOfThisYearWise.objects.filter(
                organization_id=organization,
                leave_date__date=today,
                is_active=True
            ).exists()

            if is_today_holiday:
                attendance.present_one = "Absent"
                attendance.present_two = "Absent"
                attendance.save()
                return Response({"message": "Marked absent due to holiday"}, status=status.HTTP_200_OK)

            if is_check_in:
                attendance.check_in_time = punch_time.time()

                if config.punch_in_start_time <= punch_time.time() <= config.punch_in_end_time:
                    attendance.present_one = "Present"
                elif config.punch_in_start_late_time and config.punch_in_end_late_time:
                    if config.punch_in_start_late_time <= punch_time.time() <= config.punch_in_end_late_time:
                        attendance.present_one = "Late"
                    elif punch_time.time() > config.punch_in_end_late_time:
                        attendance.present_one = "Absent"
            else:
                attendance.check_out_time = punch_time.time()

                if config.punch_out_start_time <= punch_time.time() <= config.punch_out_end_time:
                    attendance.present_two = "Present"
                elif punch_time.time() < config.punch_out_start_time:
                    attendance.present_two = "Early"
                elif config.over_time_working_end_time:
                    punch_out_end_dt = datetime.combine(today, config.punch_out_end_time)
                    overtime_end_dt = datetime.combine(today, config.over_time_working_end_time)

                    if punch_time > punch_out_end_dt and punch_time <= overtime_end_dt:
                        attendance.present_two = "Present"
                        attendance.is_overtime = True
                        overtime_duration = punch_time - punch_out_end_dt
                        attendance.overtime_hours = round(overtime_duration.total_seconds() / 3600, 2)
                    elif punch_time > overtime_end_dt:
                        attendance.present_two = "Absent"

            # Calculate work_hours if both times are set
            if attendance.check_in_time and attendance.check_out_time:
                in_time = datetime.combine(today, attendance.check_in_time)
                out_time = datetime.combine(today, attendance.check_out_time)
                attendance.work_hours = round((out_time - in_time).total_seconds() / 3600, 2)

            attendance.save()
            return Response({"message": message}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class UpdateAttendanceRecordView(APIView):
    def put(self, request):
        license_key = request.data.get("license_key")
        employee_id = request.data.get("employee_id")
        date_str = request.data.get("date")

        if not all([license_key, employee_id, date_str]):
            return Response({"error": "license_key, employee_id, and date are required."}, status=status.HTTP_400_BAD_REQUEST)

        attendance_date = parsedate(date_str)
        if not attendance_date:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get organization
            license_obj = License.objects.get(key=license_key)
            organization = license_obj.organization

            # Get employee
            employee = Employees.objects.get(id=employee_id, organization=organization)

            # Get attendance record
            attendance = AttendanceRecords.objects.get(employee_id=employee, organization_id=organization, date=attendance_date)

            # Optional fields: only update if provided
            optional_fields = ['check_in_time', 'check_out_time', 'present_one', 'present_two', 'work_hours', 'is_overtime', 'overtime_hours']
            for field in optional_fields:
                if field in request.data:
                    setattr(attendance, field, request.data[field])  # Update only if present

            attendance.save()
            return Response({"message": "Attendance updated successfully."}, status=status.HTTP_200_OK)

        except License.DoesNotExist:
            return Response({"error": "Invalid license key."}, status=status.HTTP_404_NOT_FOUND)
        except Employees.DoesNotExist:
            return Response({"error": "Employee not found under this organization."}, status=status.HTTP_404_NOT_FOUND)
        except AttendanceRecords.DoesNotExist:
            return Response({"error": "Attendance record not found for given employee and date."}, status=status.HTTP_404_NOT_FOUND)

class EmployeeListView(APIView):
    def get(self, request):
        license_key = request.GET.get("license_key")
        gender = request.GET.get("gender")
        department = request.GET.get("department")
        designation = request.GET.get("designation")
        work_shift = request.GET.get("work_shift")
        print(license_key)
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
                    "leave_type": leave.leave_type.leave_type,
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
        data = request.data
        license_key = data.get("license_key")

        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization
        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

        # Inject the resolved organization into the serializer
        device_data = data.copy()
        device_data["organization_id"] = organization.id  # expected field in serializer/model

        serializer = seri.DeviceSettingSerializer(data=device_data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Device added successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    


class ListDeviceByLicenseView(APIView):
    def get(self, request):
        license_key = request.GET.get("license_key")
        
        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            license = License.objects.get(key=license_key)
            organization = license.organization
        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)
        
        devices = DeviceSetting.objects.filter(organization_id=organization).order_by("device_name")
        serializer = seri.DeviceSettingSerializer(devices, many=True)
        return Response({"devices": serializer.data}, status=status.HTTP_200_OK)
    
class UpdateDeviceView(APIView):
    def patch(self, request, pk):
        license_key = request.data.get("license_key")

        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization
        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

        try:
            device = DeviceSetting.objects.get(pk=pk, organization_id=organization)
        except DeviceSetting.DoesNotExist:
            return Response({"error": "Device not found for this organization"}, status=status.HTTP_404_NOT_FOUND)

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
                department_name=department_name,
                organization_id=license.organization
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
            designation_name = request.data.get("designation_name")

            if not license_key or not designation_name:
                return Response({"error": "License key and designation name are required"}, status=400)

            try:
                license = License.objects.get(key=license_key)
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=400)

            designation = Designation.objects.create(
                designation_name=designation_name,
                organization_id=license.organization
            )

            return Response({"message": "Designation added successfully", "id": designation.id}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# ----------------- Update Designation -----------------
class UpdateDesignationView(APIView):
    def put(self, request, designation_id):
        try:
            designation_name = request.data.get("designation_name")
            if not designation_name:
                return Response({"error": "Designation name is required"}, status=400)

            try:
                designation = Designation.objects.get(id=designation_id)
            except Designation.DoesNotExist:
                return Response({"error": "Designation not found"}, status=404)

            designation.designation_name = designation_name
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

class ListDepartmentsByLicenseView(APIView):
    def get(self, request):
        license_key = request.GET.get("license_key")
        
        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization

            departments = Department.objects.filter(organization_id=organization, is_active=True)
            department_list = [
                {"id": dept.id, "department_name": dept.department_name}
                for dept in departments
            ]

            return Response({"departments": department_list}, status=status.HTTP_200_OK)

        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListDesignationsByLicenseView(APIView):
    def get(self, request):
        license_key = request.GET.get("license_key")
        
        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization

            designations = Designation.objects.filter(organization_id=organization, is_active=True)
            designation_list = [
                {"id": desg.id, "designation_name": desg.designation_name}
                for desg in designations
            ]

            return Response({"designations": designation_list}, status=status.HTTP_200_OK)

        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)
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
                created_date__year=current_year,
                created_date__month=current_month
            ).count()

            # 8. Late Check-ins Today
            late_checkins = todays_attendance.filter(present_one="Late").count()

            # 9. Active Devices Today
            active_devices_today = DeviceSetting.objects.filter(
                organization_id=organization,
                last_sync_interval__date=today
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

            # Update flow
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

            # Check if leave type already exists for this employee
            existing = EmployeeLeaveDetails.objects.filter(
                employee_id=employee.user,
                employee_leave_type=leave_type
            ).first()

            if existing:
                return Response(
                    {"error": f"Leave type '{leave_type.leave_type}' already exists for this employee."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create new leave detail
            leave_detail = EmployeeLeaveDetails.objects.create(
                employee_id=employee.user,
                employee_leave_type=leave_type,
                leave_count=leave_count
            )
            return Response(
                {"message": "Leave detail created", "leave_detail_id": leave_detail.id},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

class RequestLeaveAPIView(APIView):
    def post(self, request):
        try:
            data = request.data
            print(data)
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
        


class ListConfigurationByLicenseKeyView(APIView):
    def get(self, request):
        license_key = request.GET.get("license_key")

        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization

            configs = Configuration.objects.filter(organization_id=organization)

            result = []
            for config in configs:
                result.append({
                    "id": config.id,
                    "workshift": config.workshift,
                    "punch_in_start_time": str(config.punch_in_start_time) if config.punch_in_start_time else None,
                    "punch_in_end_time": str(config.punch_in_end_time) if config.punch_in_end_time else None,
                    "punch_in_start_late_time": str(config.punch_in_start_late_time) if config.punch_in_start_late_time else None,
                    "punch_in_end_late_time": str(config.punch_in_end_late_time) if config.punch_in_end_late_time else None,
                    "punch_out_start_time": str(config.punch_out_start_time) if config.punch_out_start_time else None,
                    "punch_out_end_time": str(config.punch_out_end_time) if config.punch_out_end_time else None,
                    "over_time_working_end_time": str(config.over_time_working_end_time) if config.over_time_working_end_time else None,
                })

            return Response({"configurations": result}, status=status.HTTP_200_OK)

        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
class AddOrUpdateHolidayView(APIView):
    def post(self, request):
        try:
            data = request.data
            license_key = data.get("license_key")
            leave_name = data.get("leave_name")
            leave_date = data.get("leave_date")  
            leave_id = data.get("id")  # Optional
            created_by_id = data.get("created_by")

            if not (license_key and leave_name and leave_date and created_by_id):
                return Response({"error": "Required fields: license_key, leave_name, leave_date, created_by"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate license
            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

            leave_date = parse_date(leave_date)  
            if not leave_date:
                return Response({"error": "Invalid leave_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            created_by = CustomUser.objects.get(id=created_by_id)

            if leave_id:
                # Update
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
                # Create
                existing = leaveDaysOfThisYearWise.objects.filter(
                    organization_id=organization,
                    leave_date=leave_date  
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



def get_first_day_and_today():
    today = date.today()
    first_day = today.replace(day=1)
    return first_day, today


def calculate_attendance_metrics(employee, start_date, end_date):
    attendance = AttendanceRecords.objects.filter(
        employee_id=employee,
        date__range=(start_date, end_date)
    )
    full_day = 0
    half_day = 0
    total_hours = 0
    overtime = 0

    for record in attendance:
        if record.present_one == "Present" and record.present_two == "Present":
            full_day += 1
        elif record.present_one == "Present" or record.present_two == "Present":
            half_day += 1
        total_hours += record.work_hours or 0
        overtime += record.overtime_hours or 0

    return full_day, half_day, total_hours, overtime


class GenerateOrUpdatePayrollView(APIView):
    def post(self, request):
        license_key = request.data.get("license_key")
        specific_employee_id = request.data.get("employee_id")  # optional

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization
        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_400_BAD_REQUEST)

        start_date, end_date = get_first_day_and_today()
        total_working_days = (end_date - start_date).days + 1

        employees = Employees.objects.filter(organization=organization)
        if specific_employee_id:
            employees = employees.filter(id=specific_employee_id)

        updated_employees = []
        for employee in employees:
            full_day, half_day, total_hours, overtime_hours = calculate_attendance_metrics(
                employee, start_date, end_date
            )

            days_worked = full_day + (half_day * 0.5)
            salary_per_day = employee.basic_salary / total_working_days
            earned_salary = salary_per_day * days_worked
            overtime_amount = employee.over_time_salary * overtime_hours
            gosi_deduction = employee.gosi_deduction_amount if employee.gosi_applicable else 0
            net_salary = earned_salary + overtime_amount - gosi_deduction

            payroll, created = PayrollRecords.objects.update_or_create(
                organization_id=organization,
                employee_id=employee,
                month=start_date,
                defaults={
                    "basic_salary": employee.basic_salary,
                    "total_days": total_working_days,
                    "present_days": days_worked,
                    "absent_days": total_working_days - days_worked,
                    "allowance": 0,
                    "deduction": gosi_deduction,
                    "net_salary": round(net_salary, 2),
                    "total_overtime_hours": overtime_hours,
                    "over_time_salary": overtime_amount,
                    "total_working_hours": total_hours,
                    "payroll_generated": True
                },
            )

            updated_employees.append({
                "employee_id": employee.id,
                "name": employee.full_name,
                "net_salary": payroll.net_salary,
                "payroll_status": "Updated" if not created else "Created"
            })

        return Response({
            "status": "success",
            "organization": organization.organization_name,
            "payroll": updated_employees
        }, status=status.HTTP_200_OK)





class AddOrUpdateLeaveTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            license_key = data.get("license_key")
            leave_type = data.get("leave_type")

            if not license_key or not leave_type:
                return Response({"error": "Both license_key and leave_type are required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                license = License.objects.get(key=license_key)
                organization = license.organization
            except License.DoesNotExist:
                return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)

            leave_type = leave_type.strip().upper()

            try:
                leave_obj = LEAVETYPE.objects.get(leave_type=leave_type, organization_id=organization)
                is_update = True
            except LEAVETYPE.DoesNotExist:
                leave_obj = LEAVETYPE(organization_id=organization, leave_type=leave_type)
                is_update = False

            leave_obj.is_active = data.get("is_active", True)
            leave_obj.save()

            return Response({
                "message": f"Leave type {'updated' if is_update else 'added'} successfully",
                "leave_type": leave_obj.leave_type,
                "organization": organization.organization_name
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ListLeaveTypesByLicenseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        license_key = request.GET.get("license_key")

        if not license_key:
            return Response({"error": "license_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            license = License.objects.get(key=license_key)
            organization = license.organization

            leave_types = LEAVETYPE.objects.filter(organization_id=organization)

            result = []
            for lt in leave_types:
                result.append({
                    "id": lt.id,
                    "leave_type": lt.leave_type,
                    "is_active": lt.is_active
                })

            return Response({"leave_types": result}, status=status.HTTP_200_OK)

        except License.DoesNotExist:
            return Response({"error": "Invalid license key"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)