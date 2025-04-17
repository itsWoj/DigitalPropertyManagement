import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Tenant, MaintenanceRequest
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

# Temporary users
sample_users = {
    "admin001": "pass1234",
    "tech001": "tooltime",
    "tenant009": "secureme"
}

#Admin Login - Admin 12345

@csrf_exempt  #remove when project done
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = data.get("userID")
        password = data.get("password")

        # Check if the user exists and password matches
        if sample_users.get(user_id) == password:
            return JsonResponse({"message": "Login successful", "userID": user_id}, status=200)
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=401)
    return JsonResponse({"error": "Invalid method"}, status=405)


def assign_technician(request):
    pass  


@login_required
def tenant_dashboard(request):
    try:
        tenant = Tenant.objects.get(user=request.user)
        maintenance_requests = MaintenanceRequest.objects.filter(tenant=tenant)
    except Tenant.DoesNotExist:
        maintenance_requests = []

    return render(request, 'tenant_dashboard.html', {
        'requests': maintenance_requests
    })

def tenant_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('tenant_dashboard')  # use your dashboard URL name
        else:
            messages.error(request, "Invalid credentials")
            return redirect('tenant_login')  # use your login URL name

    return render(request, 'tenant_login.html')  # login form
