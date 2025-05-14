from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
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

        