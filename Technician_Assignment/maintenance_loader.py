from Technician_Assignment.maintenance_request import MaintenanceRequest

def get_test_request():
    return MaintenanceRequest(
        skillset='Plumbing',
        rating=4,
        urgency=3,
        zone='Uptown'
    )
