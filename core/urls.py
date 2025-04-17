from django.urls import path
from . import views
from .views import tenant_dashboard
from .views import tenant_login_view
from .views import assign_technician


urlpatterns = [
    path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('tenant/login/', tenant_login_view, name='tenant_login'),
    path('api/login/', views.login_user, name='login'), 
    path('api/assign-technician/', assign_technician),
]
