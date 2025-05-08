from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # this allows routes like /tenant/login/
    path('api/', include('core.urls')),  # this allows routes like /api/login/
]
