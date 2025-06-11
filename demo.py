from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import (
    CustomUser, Employees, Department, Designation, 
    LEAVETYPE, EmployeeLeaveDetails, GENDER_CHOICE
)
from django.core.exceptions import ValidationError
import json
from datetime import datetime

class AddEmployeeView(View):
    """
    View to handle both user creation and employee details in a single operation
    """
    
    def get(self, request):
        """Render the add employee form"""
        context = {
            'departments': Department.objects.filter(is_active=True),
            'designations': Designation.objects.filter(is_active=True),
            'leave_types': LEAVETYPE.objects.filter(is_active=True),
            'gender_choices': GENDER_CHOICE,
        }
        return render(request, 'employees/add_employee.html', context)
    
    @transaction.atomic
    def post(self, request):
        """Handle form submission for creating user and employee"""
        try:
            # Extract user data
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            user_type = request.POST.get('user_type', 'employee')
            
            # Extract employee data
            full_name = request.POST.get('full_name')
            department_id = request.POST.get('department')
            designation_id = request.POST.get('designation')
            date_of_birth = request.POST.get('date_of_birth')
            gender = request.POST.get('gender')
            nationality = request.POST.get('nationality')
            iqama_number = request.POST.get('iqama_number')
            mob_no = request.POST.get('mob_no')
            joining_date = request.POST.get('joining_date')
            basic_salary = request.POST.get('basic_salary', 0)
            gosi_applicable = request.POST.get('gosi_applicable') == 'on'
            filename = request.POST.get('filename', '')
            file = request.FILES.get('file')
            
            # Validate required fields
            if not all([username, email, password, first_name, last_name, full_name, 
                       department_id, designation_id, date_of_birth, joining_date]):
                messages.error(request, "All required fields must be filled.")
                return self.get(request)
            
            # Check if username or email already exists
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return self.get(request)
            
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
                return self.get(request)
            
            # Create user first
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type
            )
            
            # Get department and designation objects
            department = get_object_or_404(Department, id=department_id, is_active=True)
            designation = get_object_or_404(Designation, id=designation_id, is_active=True)
            
            # Convert date strings to datetime objects
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
            join_date = datetime.strptime(joining_date, '%Y-%m-%d')
            
            # Create default employee leave details first
            default_leave_details = self.create_default_leave_details(user)
            
            # Create employee record
            employee = Employees.objects.create(
                user=user,
                full_name=full_name,
                department=department,
                designation=designation,
                date_of_birth=dob,
                gender=gender,
                nationality=nationality,
                iqama_number=iqama_number,
                mob_no=mob_no,
                joining_date=join_date,
                basic_salary=float(basic_salary) if basic_salary else 0,
                gosi_applicable=gosi_applicable,
                filename=filename,
                file=file,
                employee_leave_details=default_leave_details
            )
            
            messages.success(request, f"Employee {full_name} created successfully!")
            return redirect('employee_list')  # Redirect to employee list page
            
        except ValidationError as e:
            messages.error(request, f"Validation Error: {str(e)}")
            return self.get(request)
        except Exception as e:
            messages.error(request, f"Error creating employee: {str(e)}")
            return self.get(request)
    
    def create_default_leave_details(self, user):
        """Create default leave details for new employee"""
        # Get the first available leave type or create a default one
        try:
            default_leave_type = LEAVETYPE.objects.filter(is_active=True).first()
            if not default_leave_type:
                # Create a default leave type if none exists
                default_leave_type = LEAVETYPE.objects.create(
                    leave_type='ANNUAL',
                    is_active=True
                )
            
            # Create employee leave details with default values
            leave_details = EmployeeLeaveDetails.objects.create(
                employee_id=user,
                employee_leave_type=default_leave_type,
                leave_count=21  # Default 21 days annual leave
            )
            return leave_details
            
        except Exception as e:
            raise ValidationError(f"Error creating leave details: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class AddEmployeeAjaxView(View):
    """
    AJAX version of the add employee view for better UX
    """
    
    @transaction.atomic
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Extract and validate data
            user_data = data.get('user', {})
            employee_data = data.get('employee', {})
            
            # Validate required fields
            required_user_fields = ['username', 'email', 'password', 'first_name', 'last_name']
            required_employee_fields = ['full_name', 'department_id', 'designation_id', 
                                      'date_of_birth', 'joining_date']
            
            for field in required_user_fields:
                if not user_data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'message': f'{field.replace("_", " ").title()} is required'
                    })
            
            for field in required_employee_fields:
                if not employee_data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'message': f'{field.replace("_", " ").title()} is required'
                    })
            
            # Check for existing username/email
            if CustomUser.objects.filter(username=user_data['username']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                })
            
            if CustomUser.objects.filter(email=user_data['email']).exists():
                return JsonResponse({
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
            
            # Create default leave details
            default_leave_details = self.create_default_leave_details(user)
            
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
                employee_leave_details=default_leave_details
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Employee {employee.full_name} created successfully!',
                'employee_id': employee.id
            })
            
        except Department.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Selected department does not exist'
            })
        except Designation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Selected designation does not exist'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating employee: {str(e)}'
            })
    
    def create_default_leave_details(self, user):
        """Create default leave details for new employee"""
        try:
            default_leave_type = LEAVETYPE.objects.filter(is_active=True).first()
            if not default_leave_type:
                default_leave_type = LEAVETYPE.objects.create(
                    leave_type='ANNUAL',
                    is_active=True
                )
            
            leave_details = EmployeeLeaveDetails.objects.create(
                employee_id=user,
                employee_leave_type=default_leave_type,
                leave_count=21
            )
            return leave_details
            
        except Exception as e:
            raise ValidationError(f"Error creating leave details: {str(e)}")


# Function-based view alternative
@login_required
@transaction.atomic
def add_employee_function_view(request):
    """
    Function-based view for adding employee
    """
    if request.method == 'GET':
        context = {
            'departments': Department.objects.filter(is_active=True),
            'designations': Designation.objects.filter(is_active=True),
            'leave_types': LEAVETYPE.objects.filter(is_active=True),
            'gender_choices': GENDER_CHOICE,
        }
        return render(request, 'employees/add_employee.html', context)
    
    elif request.method == 'POST':
        try:
            # User creation
            user = CustomUser.objects.create_user(
                username=request.POST['username'],
                email=request.POST['email'],
                password=request.POST['password'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                user_type=request.POST.get('user_type', 'employee')
            )
            
            # Employee creation
            department = Department.objects.get(id=request.POST['department'])
            designation = Designation.objects.get(id=request.POST['designation'])
            
            # Create default leave details
            default_leave_type = LEAVETYPE.objects.filter(is_active=True).first()
            if not default_leave_type:
                default_leave_type = LEAVETYPE.objects.create(leave_type='ANNUAL')
            
            leave_details = EmployeeLeaveDetails.objects.create(
                employee_id=user,
                employee_leave_type=default_leave_type,
                leave_count=21
            )
            
            employee = Employees.objects.create(
                user=user,
                full_name=request.POST['full_name'],
                department=department,
                designation=designation,
                date_of_birth=datetime.strptime(request.POST['date_of_birth'], '%Y-%m-%d'),
                gender=request.POST.get('gender'),
                nationality=request.POST.get('nationality'),
                iqama_number=request.POST.get('iqama_number'),
                mob_no=request.POST.get('mob_no'),
                joining_date=datetime.strptime(request.POST['joining_date'], '%Y-%m-%d'),
                basic_salary=float(request.POST.get('basic_salary', 0)),
                gosi_applicable=request.POST.get('gosi_applicable') == 'on',
                filename=request.POST.get('filename', ''),
                file=request.FILES.get('file'),
                employee_leave_details=leave_details
            )
            
            messages.success(request, f"Employee {employee.full_name} created successfully!")
            return redirect('employee_list')
            
        except Exception as e:
            messages.error(request, f"Error creating employee: {str(e)}")
            return render(request, 'employees/add_employee.html', {
                'departments': Department.objects.filter(is_active=True),
                'designations': Designation.objects.filter(is_active=True),
                'gender_choices': GENDER_CHOICE,
            })


# Utility function to create multiple employees (bulk creation)
@transaction.atomic
def bulk_create_employees(employee_data_list):
    """
    Utility function for bulk employee creation
    employee_data_list: List of dictionaries containing employee data
    """
    created_employees = []
    errors = []
    
    for data in employee_data_list:
        try:
            # Create user
            user = CustomUser.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data.get('password', 'default123'),
                first_name=data['first_name'],
                last_name=data['last_name'],
                user_type=data.get('user_type', 'employee')
            )
            
            # Create leave details
            default_leave_type = LEAVETYPE.objects.filter(is_active=True).first()
            leave_details = EmployeeLeaveDetails.objects.create(
                employee_id=user,
                employee_leave_type=default_leave_type,
                leave_count=21
            )
            
            # Create employee
            employee = Employees.objects.create(
                user=user,
                full_name=data['full_name'],
                department_id=data['department_id'],
                designation_id=data['designation_id'],
                date_of_birth=data['date_of_birth'],
                gender=data.get('gender'),
                nationality=data.get('nationality'),
                iqama_number=data.get('iqama_number'),
                mob_no=data.get('mob_no'),
                joining_date=data['joining_date'],
                basic_salary=data.get('basic_salary', 0),
                gosi_applicable=data.get('gosi_applicable', True),
                employee_leave_details=leave_details
            )
            
            created_employees.append(employee)
            
        except Exception as e:
            errors.append(f"Error creating employee {data.get('full_name', 'Unknown')}: {str(e)}")
    
    return created_employees, errors