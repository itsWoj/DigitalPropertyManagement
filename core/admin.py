from django.contrib import admin
from .models import Property, PropertyManager, Technician, Tenant, MaintenanceRequest, Assignment, TechnicianRating, TechnicianAssignmentState

from django.contrib import admin

admin.site.site_header = "Property Maintenance Portal"
admin.site.site_title = "PMP Admin"
admin.site.index_title = "Welcome to the Maintenance Management System"

admin.site.register(Property)
admin.site.register(PropertyManager)
admin.site.register(Technician)
admin.site.register(Tenant)
admin.site.register(MaintenanceRequest)
admin.site.register(Assignment)
admin.site.register(TechnicianRating)
admin.site.register(TechnicianAssignmentState)
