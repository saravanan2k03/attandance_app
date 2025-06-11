import copy
from datetime import datetime
from tokenize import TokenError
from django.http import HttpResponse, Response
from django.shortcuts import render
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

from attendanceapp.models import LEAVETYPE, CustomUser, Department, Designation, EmployeeLeaveDetails, Employees
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


class AddEmployeeData(APIView):
    permission_classes = (IsAuthenticated)
    
    def post(self, request):
        try:
            
            # Extract and validate data
            user_data = request.data('user', {})
            employee_data = request.data('employee', {})
            
            # Validate required fields
            required_user_fields = ['username', 'email', 'password', 'first_name', 'last_name']
            required_employee_fields = ['full_name', 'department_id', 'designation_id', 
                                      'date_of_birth', 'joining_date']
            
            for field in required_user_fields:
                if not user_data.get(field):
                    return Response({
                        'success': False, 
                        'message': f'{field.replace("_", " ").title()} is required'
                    })
            
            for field in required_employee_fields:
                if not employee_data.get(field):
                    return Response({
                        'success': False, 
                        'message': f'{field.replace("_", " ").title()} is required'
                    })
            
            # Check for existing username/email
            if CustomUser.objects.filter(username=user_data['username']).exists():
                return Response({
                    'success': False,
                    'message': 'Username already exists'
                })
            
            if CustomUser.objects.filter(email=user_data['email']).exists():
                return Response({
                    'success': False,
                    'message': 'Email already exists'
                })
            
            # Create user
            user = CustomUser.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                user_type=user_data.get('user_type', 'employee')
            )
            
            # Get related objects
            department = Department.objects.get(
                id=employee_data['department_id'], 
                is_active=True
            )
            designation = Designation.objects.get(
                id=employee_data['designation_id'], 
                is_active=True
            )
            for element in employee_data['']:
                default_leave_type = LEAVETYPE.objects.get(
                leave_type = element[''],
                is_active=True
                )
                leave_details = EmployeeLeaveDetails.objects.create(
                    employee_id=user,
                    employee_leave_type=default_leave_type,
                    leave_count=element['count']  # Default 21 days annual leave
                )               
                            
            # Create employee
            employee = Employees.objects.create(
                user=user,
                full_name=employee_data['full_name'],
                department=department,
                designation=designation,
                date_of_birth=datetime.strptime(employee_data['date_of_birth'], '%Y-%m-%d'),
                gender=employee_data.get('gender'),
                nationality=employee_data.get('nationality'),
                iqama_number=employee_data.get('iqama_number'),
                mob_no=employee_data.get('mob_no'),
                joining_date=datetime.strptime(employee_data['joining_date'], '%Y-%m-%d'),
                basic_salary=float(employee_data.get('basic_salary', 0)),
                gosi_applicable=employee_data.get('gosi_applicable', True),
                filename=employee_data.get('filename', ''),
            )
            
            return Response({
                'success': True,
                'message': f'Employee {employee.full_name} created successfully!',
                'employee_id': employee.id
            })
            
        except Department.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Selected department does not exist'
            })
        except Designation.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Selected designation does not exist'
            })
        except LEAVETYPE.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Selected Leave type does not exist'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error creating employee: {str(e)}'
            })        







       