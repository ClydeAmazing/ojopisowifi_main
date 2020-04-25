from django.shortcuts import redirect
from django.views import View
from django.http import HttpResponse


class Main(View):

    def get(settings, request):
        return redirect ('http://10.0.0.1:2050/portal.html')