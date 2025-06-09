import copy
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions
from attendanceapp import serializers as seri 
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, login


# Create your views here.
def members(request):
    return HttpResponse("Hello world!")



class AuthUserView(APIView):
    @csrf_exempt
    def options(self, request, *args, **kwargs):
        print("Saravanan")

    def post(self, request, *args, **kwargs):
        try:
           request.data.get('req_from_native', False)

           return None
        except Exception as er:
            print("Err")


class RegisterUserView(APIView):
    permission_classes = [permissions.AllowAny]

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        params = copy.deepcopy(request.data)
        serializer = seri.CustomUserSerializer(data=params)

        if serializer.is_valid():
            user = serializer.save()

            refreshToken = RefreshToken.for_user(user)

            return Response({'statusCode':201,"user":serializer.data,"token":{"access_token":str(refreshToken.access_token),"refresh_token":str(refreshToken)}})
        else:
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
        

class LoginUserView(APIView):

    @csrf_exempt
    def post(self, request, *args, **kwargs):

        username = request.data.get('username')
        password = request.data.get('password')

        if username or password:
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(username=username)
                serializer = seri.CustomUserSerializer(user)
                refresh = RefreshToken.for_user(user)
                return Response({'statusCode':201,"user":serializer.data,"token":{"access_token":str(refresh.access_token),"refresh_token":str(refresh)}})

            except UserModel.DoesNotExist as uEr:
                return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)



           



        











       