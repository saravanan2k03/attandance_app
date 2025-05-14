from rest_framework import serializers

from attendanceapp import models



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