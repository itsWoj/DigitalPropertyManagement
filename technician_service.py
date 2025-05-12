from datetime import datetime, timedelta
from db import get_db_connection

def complete_old_requests():
    """Mark old requests as completed and free up technicians"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            UPDATE MaintenanceRequests 
            SET Status = 'Completed', 
                CompletedAt = NOW() 
            WHERE Status = 'InProgress' 
            AND CreatedAt < NOW() - INTERVAL 1 DAY
        """)
        
        cursor.execute("""
            UPDATE Technicians t
            JOIN MaintenanceRequests mr ON t.TechnicianID = mr.TechnicianID
            SET t.Status = 'Free'
            WHERE mr.Status = 'Completed'
            AND t.Status = 'Busy'
        """)
        
        conn.commit()
        return cursor.rowcount

def assign_technician(request_data):
    """Assign best technician to a new request"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        complete_old_requests()
        
        cursor.execute("""
            SELECT t.*, u.FirstName, u.LastName
            FROM Technicians t
            JOIN Users u ON t.UserID = u.UserID
            WHERE t.Status = 'Free'
            AND t.Skillset = %s
            AND t.Zone = %s
            ORDER BY t.Rating DESC
            LIMIT 1
        """, (request_data['skillset'], request_data['zone']))
        
        technician = cursor.fetchone()
        
        if not technician:
            raise Exception("No available technicians")
        
        cursor.execute("""
            INSERT INTO MaintenanceRequests (
                TenantID, Skillset, Description, Zone, Urgency,
                TechnicianID, Status, CreatedAt
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending', NOW())
        """, (
            request_data['tenant_id'],
            request_data['skillset'],
            request_data['description'],
            request_data['zone'],
            request_data['urgency'],
            technician['TechnicianID']
        ))
        
        cursor.execute("""
            UPDATE Technicians 
            SET Status = 'Busy' 
            WHERE TechnicianID = %s
        """, (technician['TechnicianID'],))
        
        conn.commit()
        return cursor.lastrowid  

def update_technician_ratings():
    """Update all technician ratings based on completed jobs"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            UPDATE Technicians t
            SET t.Rating = (
                SELECT COALESCE(AVG(mr.Rating), 3.0)
                FROM MaintenanceRequests mr
                WHERE mr.TechnicianID = t.TechnicianID
                AND mr.Rating IS NOT NULL
            )
            WHERE EXISTS (
                SELECT 1 FROM MaintenanceRequests mr
                WHERE mr.TechnicianID = t.TechnicianID
            )
        """)
        
        conn.commit()
        return cursor.rowcount