from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

from django.conf.urls.static import static
from django.conf import settings

from .views import * 

urlpatterns = [
    path('app/', include('app.urls')),
    path('app/admin/', admin.site.urls),
    # path('', Main.as_view())
    path('', RedirectView.as_view(url='/app/portal')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
