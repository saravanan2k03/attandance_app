import copy
from datetime import datetime
from tokenize import TokenError
from django.http import HttpResponse, Response
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

from attendanceapp.models import LEAVETYPE, AttendanceRecords, CustomUser, Department, Designation, DeviceSetting, EmployeeLeaveDetails, Employees, LeaveMangement
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


class AddEmployeeView(APIView):
    def post(self, request):
        try:
            data = request.data

            # Create User
            user = CustomUser.objects.create(
                username=data["username"],
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                user_type="employee",
                password=make_password(data["password"]),
            )

            # Foreign Keys
            department = Department.objects.get(id=data["department_id"])
            designation = Designation.objects.get(id=data["designation_id"])

            # Create Employee
            employee = Employees.objects.create(
                user=user,
                full_name=f"{data['first_name']} {data['last_name']}",
                department=department,
                designation=designation,
                date_of_birth=data["date_of_birth"],
                gender=data["gender"],
                nationality=data.get("nationality", ""),
                iqama_number=data.get("iqama_number", ""),
                mob_no=data.get("mob_no", ""),
                joining_date=data["joining_date"],
                work_status=data.get("work_status", True),
                basic_salary=data.get("basic_salary", 0.0),
                gosi_applicable=data.get("gosi_applicable", True),
                filename=data.get("filename", ""),
                file=data.get("file", None),
            )

            # Create Leave Details
            leave_details = data.get("leave_details", [])
            for leave_entry in leave_details:
                leave_type_name = leave_entry.get("leave_type")
                leave_count = leave_entry.get("leave_count", 0)

                leave_type = LEAVETYPE.objects.get(leave_type=leave_type_name.upper())

                EmployeeLeaveDetails.objects.create(
                    employee_id=user,
                    employee_leave_type=leave_type,
                    leave_count=leave_count
                )

            return Response({"message": "Employee and leave details added successfully"}, status=status.HTTP_201_CREATED)

        except Department.DoesNotExist:
            return Response({"error": "Department not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Designation.DoesNotExist:
            return Response({"error": "Designation not found"}, status=status.HTTP_400_BAD_REQUEST)
        except LEAVETYPE.DoesNotExist as e:
            return Response({"error": f"Leave type not found: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

###########need to Work###################
class AddAttendanceRecordView(APIView):
    def post(self, request):
        try:
            data = request.data
            employee_id = data.get("employee_id")

            # Check if employee exists
            try:
                employee = Employees.objects.get(id=employee_id)
            except Employees.DoesNotExist:
                return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

            # Create attendance record
            attendance = AttendanceRecords.objects.create(
                employee_id=employee,
                check_in_time=data["check_in_time"],
                check_out_time=data["check_out_time"],
                work_hours=data.get("work_hours", 0),
                overtime_hours=data.get("overtime_hours", 0),
                status=data.get("status", "Present")
            )

            return Response({"message": "Attendance record added successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class EmployeeListView(APIView):
    def get(self, request):
        gender = request.GET.get("gender")
        department = request.GET.get("department")
        designation = request.GET.get("designation")
        work_shift = request.GET.get("work_shift")

        employees = Employees.objects.all()

        if gender:
            employees = employees.filter(gender=gender)
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

class EmployeeLeaveManagementFilterView(APIView):
    def get(self, request, employee_id):
        leave_type_filter = request.GET.get('category')  # optional query param

        try:
            employee = Employees.objects.get(id=employee_id)
            leave_qs = LeaveMangement.objects.filter(employee_id=employee).order_by('start_date')

            if leave_type_filter:
                leave_qs = leave_qs.filter(leave_type__iexact=leave_type_filter)

            if not leave_qs.exists():
                return Response({"message": "No leave records found for this employee."}, status=status.HTTP_404_NOT_FOUND)

            serializer = seri.LeaveManagementSerializer(leave_qs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Employees.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
        

class AllEmployeeLeaveManagementFilterView(APIView):
    def get(self, request, employee_id):
        leave_type_filter = request.GET.get('category')  # optional query param

        try:
            leave_qs = LeaveMangement.objects.all().order_by('start_date')

            if leave_type_filter:
                leave_qs = leave_qs.filter(leave_type__iexact=leave_type_filter)

            if not leave_qs.exists():
                return Response({"message": "No leave records found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = seri.LeaveManagementSerializer(leave_qs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except LeaveMangement.DoesNotExist:
            return Response({"error": "No leave records found."}, status=status.HTTP_404_NOT_FOUND)
        



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