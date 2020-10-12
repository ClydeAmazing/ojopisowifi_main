from django.urls import path
from app.api.views import DashboardDetails 

urlpatterns = [
	path('dashboard_data/', DashboardDetails.as_view()),
]