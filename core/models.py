from django.db import models
from django.contrib.auth.models import User


# ─── PROPERTY AND MANAGEMENT MODELS ─────────────────────────────────────────────
class Property(models.Model):
    property_id = models.AutoField(primary_key=True)
    location = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    expenses = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.location}"


class PropertyManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    properties_managed = models.ManyToManyField(Property)

    def __str__(self):
        return f"Manager: {self.user.username}"


# ─── TENANT MODEL ───────────────────────────────────────────────────────────────
class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    rent = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Tenant: {self.user.username}"


# ─── TECHNICIAN MODEL ───────────────────────────────────────────────────────────
class Technician(models.Model):
    technician_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    skillset = models.TextField()
    location = models.CharField(max_length=255)
    availability = models.BooleanField(default=True)
    current_workload = models.IntegerField(default=0)
    matrix_score = models.FloatField(default=0.0)  # Represents MatrixFactorScore

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# ─── MAINTENANCE REQUEST AND ASSIGNMENTS ────────────────────────────────────────
class MaintenanceRequest(models.Model):
    URGENCY_LEVEL = (
        (1, "Low"),
        (2, "Medium"),
        (3, "High"),
    )

    req_id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    req_type = models.CharField(max_length=100)
    description = models.TextField()
    urgency = models.IntegerField(choices=URGENCY_LEVEL)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Pending")

    def __str__(self):
        return f"Request #{self.req_id} ({self.req_type})"


class Assignment(models.Model):
    request = models.OneToOneField(MaintenanceRequest, on_delete=models.CASCADE)
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.technician} -> Request #{self.request.req_id}"


# ─── TECHNICIAN RATING ──────────────────────────────────────────────────────────
class TechnicianRating(models.Model):
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    rating = models.FloatField()  # rating 1.0 to 5.0
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('technician', 'tenant')

    def __str__(self):
        return f"Rating: {self.rating} - {self.technician} by {self.tenant}"


# ─── TECHNICIAN ASSIGNMENT HISTORY & STATE ──────────────────────────────────────


class TechnicianAssignmentState(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.key} = {self.value}"



