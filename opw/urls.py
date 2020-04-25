from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from .views import * 

urlpatterns = [
    path('app/', include('app.urls')),
    path('app/admin/', admin.site.urls),
    # path('', Main.as_view())
    path('', RedirectView.as_view(url='/app/portal')),
]
