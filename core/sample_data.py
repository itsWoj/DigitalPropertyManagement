import random
from django.contrib.auth.models import User
from core.models import Property, PropertyManager, Technician, Tenant, MaintenanceRequest

# Clear existing data (optional for dev purposes)
User.objects.all().delete()
Property.objects.all().delete()
PropertyManager.objects.all().delete()
Technician.objects.all().delete()
Tenant.objects.all().delete()
MaintenanceRequest.objects.all().delete()

# Create Properties
property1 = Property.objects.create(location="Greenview Apartments", value=250000, expenses=5000)
property2 = Property.objects.create(location="Maple Residency", value=300000, expenses=7000)

# Create Property Managers
manager1_user = User.objects.create_user(username="manager1", password="pass123")
manager1 = PropertyManager.objects.create(user=manager1_user)
manager1.properties_managed.set([property1, property2])

# Create Technicians
techs = []
for i in range(4):
    tech = Technician.objects.create(
        first_name=f"Tech{i+1}",
        last_name="Smith",
        skillset="Plumbing, Electrical",
        location="City Center",
        availability=True,
        current_workload=random.randint(0, 2)
    )
    techs.append(tech)

# Create Tenants
tenant_users = []
for i in range(3):
    user = User.objects.create_user(username=f"tenant{i+1}", password="tenantpass")
    tenant = Tenant.objects.create(user=user, property=random.choice([property1, property2]), rent=1000 + i * 100)
    tenant_users.append(tenant)

# Create Maintenance Requests
for i in range(5):
    tenant = random.choice(tenant_users)
    MaintenanceRequest.objects.create(
        tenant=tenant,
        property=tenant.property,
        req_type=random.choice(["Plumbing", "Electrical", "HVAC"]),
        description="Something needs fixing.",
        urgency=random.randint(1, 3),
    )

print("✅ Sample data created successfully!")
