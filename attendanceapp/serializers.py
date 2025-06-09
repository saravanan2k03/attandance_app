from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework.exceptions import AuthenticationFailed
from attendanceapp import models

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        return user

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=6)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise AuthenticationFailed("Invalid credentials")


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

############################################################################
class CustomUserSerializer(serializers.ModelSerializer):
     
    
    class Meta:
        model = models.CustomUser
        fields = '__all__'
        depth = 1



class EmployeesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Employees
        fields = '__all__'
        depth = 1


class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Department
        fields = '__all__'
        depth = 1



class AttendanceRecordsSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AttendanceRecords
        fields = '__all__'
        depth = 1

class PayrollRecordsAdminSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PayrollRecords
        fields = '__all__'
        depth = 1
        
class LeaveMangementAdminSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.LeaveMangement
        fields = '__all__'
        depth = 1

class LeaveMangementAdminSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.LeaveMangement
        fields = '__all__'
        depth = 1

class DeviceSettingAdminSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.DeviceSetting
        fields = '__all__'
        depth = 1