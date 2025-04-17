import random
from datetime import datetime
from django.utils.timezone import now
from django.db.models import Avg
from core.models import Technician, MaintenanceRequest, Assignment, TechnicianAssignmentState

def calculate_score(technician, request, last_assigned_id):
    # Dummy distance factor (real implementation would use geolocation)
    distance_factor = random.uniform(0.0, 1.0)

    # Matrix factor score based on ratings (default 3.0 if no ratings)
    rating = technician.rating or 3.0
    matrix_factor_score = rating / 5.0  # normalize to [0, 1]

    # Availability: 1 if available, 0 if not
    availability = 1 if technician.availability else 0

    # Urgency: scale 1 to 3, normalize to [0, 1]
    urgency = request.urgency / 3.0

    score = (0.65 * matrix_factor_score) + (0.2 * distance_factor) + availability + (0.15 * urgency)

    # Penalize if technician was last assigned
    if technician.technician_id == last_assigned_id:
        score -= 0.5

    return score

def assign_technician(request_id):
    try:
        request = MaintenanceRequest.objects.get(req_id=request_id)
        technicians = Technician.objects.filter(availability=True)

        if not technicians.exists():
            return "No technicians available"

        # Get last assigned technician ID from state
        last_assigned = TechnicianAssignmentState.objects.filter(key="last_assigned").first()
        last_assigned_id = int(last_assigned.value) if last_assigned else -1

        scored_techs = [(tech, calculate_score(tech, request, last_assigned_id)) for tech in technicians]
        scored_techs.sort(key=lambda x: x[1], reverse=True)

        # Check for tie in score
        top_score = scored_techs[0][1]
        top_candidates = [t for t, s in scored_techs if s == top_score]

        if len(top_candidates) > 1:
            top_candidates = [t for t in top_candidates if t.technician_id != last_assigned_id]
            technician = random.choice(top_candidates)
        else:
            technician = top_candidates[0]

        # Create the assignment
        assignment = Assignment.objects.create(request=request, technician=technician, assigned_at=now())

        # Save last assignment state
        TechnicianAssignmentState.objects.update_or_create(
            key="last_assigned", defaults={"value": str(technician.technician_id)}
        )

        # Update technician workload
        technician.current_workload += 1
        technician.save()

        return f"Technician {technician} assigned to request #{request_id}"

    except MaintenanceRequest.DoesNotExist:
        return "Request not found"
    except Exception as e:
        return str(e)
