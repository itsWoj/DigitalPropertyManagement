import mysql.connector
import random
from datetime import datetime, timedelta

def complete_old_requests_and_free_technicians(cursor):
    """Mark old requests as completed and free up technicians"""
    try:
        # Complete requests older than 1 day
        cursor.execute("""
            UPDATE MaintenanceRequests 
            SET Status = 'Completed', 
                CompletedAt = NOW() 
            WHERE Status = 'InProgress' 
            AND CreatedAt < NOW() - INTERVAL 1 DAY
        """)
        
        # Free up technicians from completed jobs
        cursor.execute("""
            UPDATE Technicians t
            JOIN MaintenanceRequests mr ON t.TechnicianID = mr.TechnicianID
            SET t.Status = 'Free'
            WHERE mr.Status = 'Completed'
            AND t.Status = 'Busy'
        """)
        
        return cursor.rowcount  # Number of technicians freed
        
    except Exception as e:
        raise Exception(f"Error completing old requests: {str(e)}")

def calculate_assignment_score(technician, request):
    """Calculate assignment score (0-100)"""
    if technician['Status'] == 'Busy':
        return 0

    skillset_match = 1 if technician['Skillset'] == request['Skillset'] else 0
    rating_score = technician.get('Rating', 3) / 5  # Default to 3 if no rating
    zone_match = 1 if technician['Zone'] == request['Zone'] else 0
    urgency_score = request['Urgency'] / 3

    return round(
        (skillset_match * 25) + 
        (rating_score * 25) + 
        (zone_match * 30) + 
        (urgency_score * 20),
        2
    )

def get_available_technicians(cursor, skillset, zone):
    """Get available technicians filtered by skillset and zone"""
    # First try to complete old requests and free technicians
    freed_count = complete_old_requests_and_free_technicians(cursor)
    print(f"Freed {freed_count} technicians from completed jobs")
    
    # Now get available technicians
    cursor.execute("""
        SELECT t.*, u.FirstName, u.LastName
        FROM Technicians t
        JOIN Users u ON t.UserID = u.UserID
        WHERE t.Status = 'Free' 
        AND t.Skillset = %s
        AND t.Zone = %s
    """, (skillset, zone))
    technicians = cursor.fetchall()
    
    if not technicians:
        # Fallback to any available technician with matching skillset
        cursor.execute("""
            SELECT t.*, u.FirstName, u.LastName
            FROM Technicians t
            JOIN Users u ON t.UserID = u.UserID
            WHERE t.Status = 'Free' 
            AND t.Skillset = %s
        """, (skillset,))
        technicians = cursor.fetchall()
    
    return technicians

def assign_technician(cursor, request):
    """Assign the best technician for the request"""
    technicians = get_available_technicians(
        cursor, 
        request['Skillset'], 
        request['Zone']
    )
    
    if not technicians:
        return None, 0  # No available technicians
    
    # Score and select best technician
    best_tech = max(
        technicians,
        key=lambda tech: calculate_assignment_score(tech, request)
    )
    score = calculate_assignment_score(best_tech, request)
    
    return best_tech['TechnicianID'], score

def create_maintenance_request(tenant_id, skillset, description, zone, urgency):
    """Create new maintenance request with validation"""
    conn = mysql.connector.connect(
        host="localhost",
        user="Peter",
        password="",
        database="DPM"
    )
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Validate tenant exists
        cursor.execute("SELECT TenantID FROM Tenants WHERE TenantID = %s", (tenant_id,))
        if not cursor.fetchone():
            raise ValueError(f"Tenant {tenant_id} does not exist")
        
        request_data = {
            'TenantID': tenant_id,
            'Skillset': skillset,
            'Zone': zone,
            'Urgency': urgency
        }
        
        # Assign technician (this will auto-complete old jobs first)
        tech_id, score = assign_technician(cursor, request_data)
        if not tech_id:
            raise Exception("No available technicians matching the requirements")
        
        # Create request
        cursor.execute("""
            INSERT INTO MaintenanceRequests (
                TenantID, Skillset, Description, Zone, Urgency,
                TechnicianID, Status, Score, CreatedAt
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending', %s, %s)
        """, (
            tenant_id, skillset, description, zone, urgency,
            tech_id, score, datetime.now()
        ))
        
        # Update technician status
        cursor.execute("""
            UPDATE Technicians 
            SET Status = 'Busy' 
            WHERE TechnicianID = %s
        """, (tech_id,))
        
        # Get created request
        cursor.execute("""
            SELECT r.*, u.FirstName, u.LastName
            FROM MaintenanceRequests r
            JOIN Technicians t ON r.TechnicianID = t.TechnicianID
            JOIN Users u ON t.UserID = u.UserID
            WHERE r.RequestID = LAST_INSERT_ID()
        """)
        request = cursor.fetchone()
        
        conn.commit()
        return request
        
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    try:
        # Example usage - get a valid tenant ID first
        conn = mysql.connector.connect(
            host="localhost",
            user="Peter",
            password="",
            database="DPM"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT TenantID FROM Tenants LIMIT 1")
        valid_tenant = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not valid_tenant:
            raise Exception("No tenants found in database")
        
        # Create request
        request = create_maintenance_request(
            tenant_id=valid_tenant['TenantID'],
            skillset='Plumbing',
            description='Leaking pipe in kitchen',
            zone='Uptown',
            urgency=2
        )
        
        print("\n✅ Maintenance Request Created:")
        print(f"Request ID: {request['RequestID']}")
        print(f"Assigned Technician: {request['FirstName']} {request['LastName']}")
        print(f"Assignment Score: {request['Score']}/100")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")