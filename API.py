# Author: Zedaine McDonald
import random
import string
from flask import Flask, jsonify, request, Response
import mysql.connector
from mysql.connector import Error
from typing import Dict
from Helper import get_connection, is_valid_email, generate_password
from datetime import datetime
from werkzeug.utils import secure_filename


app = Flask(__name__)

#USER CALLS
#login API call    
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Basic validation
    if not email or not password:
        return jsonify({"success": False, "message": "Please enter email and password"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT UserID, Email, Role, FirstName, LastName FROM Users WHERE Email = %s AND PasswordHash = %s"
        cursor.execute(query, (email.strip(), password.strip()))
        user = cursor.fetchone()

        if user:
            return jsonify({"success": True, "message": "Login successful", "user": user}), 200
        else:
            return jsonify({"success": False, "message": "Invalid email or password"}), 401

    except Error as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users', methods = ['POST'])
def create_user():
    data = request.get_json()

    email = data.get('email')
    role = data.get('role')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone = data.get('phone_number')

    if not email or not role:
        return jsonify({"success": False, "message": "Please enter all required fields."}), 400
    
    password = generate_password()
    
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT * FROM Users WHERE Email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "User already exists"}), 409

        # Insert new user
        cursor.execute("""
            INSERT INTO Users (Email, PasswordHash, Role, FirstName, LastName, PhoneNumber)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (email, password, role, first_name, last_name, phone))
        conn.commit()
        
         # Get UserID
        cursor.execute("SELECT LAST_INSERT_ID();")
        user_id = cursor.fetchone()[0]

        # Insert into role-specific table
        if role == "Technician":
            cursor.execute("""
                INSERT INTO Technicians (UserID, Skillset, AvgRating)
                VALUES (%s, %s, %s)
            """, (user_id, '', 0.0))

        elif role == "Tenant":
            cursor.execute("""
                INSERT INTO Tenants (UserID, PropertyID, MoveOutRequested, RentStatus)
                VALUES (%s, NULL, FALSE, 'Unpaid')
            """, (user_id,))

        elif role == "Manager":
            # Optional: hook in property assignment logic later
            pass

        conn.commit()

        return jsonify({
            "success": True,
            "message": "User created successfully.",
            "email": email,
            "role": role,
            "password": password
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"User creation failed: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()

    # Get fields from request
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone = data.get('phone_number')
    role = data.get('role')

    if not any([first_name, last_name, email, phone, role]):
        return jsonify({"success": False, "message": "No update fields provided"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        update_fields = []
        values = []

        if first_name:
            update_fields.append("FirstName = %s")
            values.append(first_name)
        if last_name:
            update_fields.append("LastName = %s")
            values.append(last_name)
        if email:
            update_fields.append("Email = %s")
            values.append(email)
        if phone:
            update_fields.append("PhoneNumber = %s")
            values.append(phone)
        if role:
            update_fields.append("Role = %s")
            values.append(role)

        values.append(user_id)

        query = f"""
            UPDATE Users SET {', '.join(update_fields)}
            WHERE UserID = %s
        """
        cursor.execute(query, tuple(values))
        conn.commit()

        return jsonify({"success": True, "message": "User profile updated successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Profile update failed: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT UserID, Email, Role, FirstName, LastName, PhoneNumber
            FROM Users
            WHERE UserID = %s
        """
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        return jsonify({"success": True, "user": user}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch user: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Optional: Check if user exists first
        cursor.execute("SELECT * FROM Users WHERE UserID = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "User not found"}), 404

        # Delete the user (will cascade to related role tables if FK is set)
        cursor.execute("DELETE FROM Users WHERE UserID = %s", (user_id,))
        conn.commit()

        return jsonify({"success": True, "message": f"User {user_id} deleted successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"User deletion failed: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>/password-reset', methods=['PUT'])
def reset_user_password(user_id):
    
    new_password = generate_password()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT * FROM Users WHERE UserID = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "User not found"}), 404

        # Update password
        cursor.execute("UPDATE Users SET PasswordHash = %s WHERE UserID = %s", (new_password, user_id))
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Password reset successfully.",
            "new password": new_password
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Password reset failed: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



#TECHNICIAN CALLS
@app.route('/api/technicians/<int:technician_id>', methods=['GET'])
def get_technician_profile(technician_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                t.TechnicianID,
                u.UserID,
                u.FirstName,
                u.LastName,
                u.Email,
                u.PhoneNumber,
                t.Skillset,
                t.AvgRating
            FROM Technicians t
            JOIN Users u ON t.UserID = u.UserID
            WHERE t.TechnicianID = %s
        """
        cursor.execute(query, (technician_id,))
        tech = cursor.fetchone()

        if not tech:
            return jsonify({"success": False, "message": "Technician not found"}), 404

        return jsonify({"success": True, "technician": tech}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch technician: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/technicians/<int:technician_id>/jobs', methods=['GET'])
def get_assigned_jobs(technician_id):
    status_filter = request.args.get('status')  # Optional query param

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        base_query = """
            SELECT 
                j.JobID,
                j.JobType,
                j.Description,
                j.Status,
                j.Urgency,
                j.RequestedTime,
                j.PropertyID,
                p.Address AS PropertyAddress,
                u.FirstName AS TenantFirstName,
                u.LastName AS TenantLastName
            FROM JobRequests j
            JOIN Properties p ON j.PropertyID = p.PropertyID
            JOIN Tenants t ON j.TenantID = t.TenantID
            JOIN Users u ON t.UserID = u.UserID
            WHERE j.AssignedTechnicianID = %s
        """

        values = [technician_id]

        if status_filter:
            base_query += " AND j.Status = %s"
            values.append(status_filter)

        base_query += " ORDER BY j.RequestedTime DESC"

        cursor.execute(base_query, tuple(values))
        jobs = cursor.fetchall()

        return jsonify({
            "success": True,
            "technician_id": technician_id,
            "filter_status": status_filter or "All",
            "assigned_jobs": jobs
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch assigned jobs: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/technicians/<int:technician_id>/schedule', methods=['POST'])
def add_technician_availability(technician_id):
    data = request.get_json()

    start_time = data.get('start_time')
    end_time = data.get('end_time')
    status = data.get('status', 'Available')  # Optional, defaults to "Available"

    if not start_time or not end_time:
        return jsonify({"success": False, "message": "Start and end time are required"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO TechnicianSchedule (TechnicianID, StartTime, EndTime, Status)
            VALUES (%s, %s, %s, %s)
        """, (technician_id, start_time, end_time, status))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Availability slot added",
            "technician_id": technician_id
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to add availability: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/technicians/<int:technician_id>/schedule', methods=['GET'])
def get_technician_schedule(technician_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT ScheduleID, StartTime, EndTime, Status
            FROM TechnicianSchedule
            WHERE TechnicianID = %s
            ORDER BY StartTime ASC
        """, (technician_id,))
        schedule = cursor.fetchall()

        return jsonify({
            "success": True,
            "technician_id": technician_id,
            "schedule": schedule
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch schedule: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



#PROPERTY CALLS
@app.route('/api/properties', methods=['GET'])
def get_all_properties():
    try:
        manager_id = request.args.get('manager_id')
        status = request.args.get('status')

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                PropertyID,
                Address,
                Latitude,
                Longitude,
                ManagerID,
                Status
            FROM Properties
            WHERE 1 = 1
        """
        values = []

        if manager_id:
            query += " AND ManagerID = %s"
            values.append(manager_id)

        if status:
            query += " AND Status = %s"
            values.append(status)

        query += " ORDER BY PropertyID ASC"

        cursor.execute(query, tuple(values))
        properties = cursor.fetchall()

        return jsonify({
            "success": True,
            "filter": {
                "manager_id": manager_id,
                "status": status
            },
            "properties": properties
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch properties: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/properties', methods=['POST'])
def add_property():
    data = request.get_json()

    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    manager_id = data.get('manager_id')
    status = data.get('status', 'Active')  # Optional, default to 'Active'

    # Basic validation
    if not address or latitude is None or longitude is None or not manager_id:
        return jsonify({"success": False, "message": "All fields are required: address, latitude, longitude, manager_id"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Properties (Address, Latitude, Longitude, ManagerID, Status)
            VALUES (%s, %s, %s, %s, %s)
        """, (address, latitude, longitude, manager_id, status))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Property added successfully",
            "property": {
                "address": address,
                "latitude": latitude,
                "longitude": longitude,
                "manager_id": manager_id,
                "status": status
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to add property: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/properties/<int:property_id>', methods=['GET'])
def get_property_by_id(property_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                PropertyID,
                Address,
                Latitude,
                Longitude,
                ManagerID,
                Status
            FROM Properties
            WHERE PropertyID = %s
        """, (property_id,))
        prop = cursor.fetchone()

        if not prop:
            return jsonify({"success": False, "message": "Property not found"}), 404

        return jsonify({"success": True, "property": prop}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch property: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/properties/<int:property_id>', methods=['PUT'])
def update_property(property_id):
    data = request.get_json()

    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    manager_id = data.get('manager_id')
    status = data.get('status')

    if not any([address, latitude, longitude, manager_id, status]):
        return jsonify({"success": False, "message": "No update fields provided"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        update_fields = []
        values = []
        changed_log = []

        if address:
            update_fields.append("Address = %s")
            values.append(address)
            changed_log.append(f"Address: {address}")
        if latitude is not None:
            update_fields.append("Latitude = %s")
            values.append(latitude)
            changed_log.append(f"Latitude: {latitude}")
        if longitude is not None:
            update_fields.append("Longitude = %s")
            values.append(longitude)
            changed_log.append(f"Longitude: {longitude}")
        if manager_id:
            update_fields.append("ManagerID = %s")
            values.append(manager_id)
            changed_log.append(f"ManagerID: {manager_id}")
        if status:
            update_fields.append("Status = %s")
            values.append(status)
            changed_log.append(f"Status: {status}")

        values.append(property_id)

        query = f"""
            UPDATE Properties SET {', '.join(update_fields)}
            WHERE PropertyID = %s
        """
        cursor.execute(query, tuple(values))

        # Log the change
        if changed_log:
            change_summary = "; ".join(changed_log)
            cursor.execute("""
                INSERT INTO PropertyUpdateLogs (PropertyID, ChangedFields, ModifiedBy)
                VALUES (%s, %s, %s)
            """, (property_id, change_summary, 'admin'))  # Replace 'admin' with actual user if available

        conn.commit()

        return jsonify({"success": True, "message": "Property updated and changes logged"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to update property: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/properties/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Optional: Check if property exists
        cursor.execute("SELECT * FROM Properties WHERE PropertyID = %s", (property_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Property not found"}), 404

        # Delete property
        cursor.execute("DELETE FROM Properties WHERE PropertyID = %s", (property_id,))
        conn.commit()

        return jsonify({
            "success": True,
            "message": f"Property {property_id} deleted successfully"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to delete property: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#TENANT CALLS
@app.route('/api/tenants', methods=['GET'])
def get_all_tenants():
    try:
        # Get query filters
        property_id = request.args.get('property_id')
        rent_status = request.args.get('rent_status')
        move_out_requested = request.args.get('move_out_requested')

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Base tenant query
        query = """
            SELECT
                t.TenantID,
                t.UserID,
                t.PropertyID,
                t.RentStatus,
                t.MoveOutRequested,
                u.FirstName,
                u.LastName,
                u.Email,
                u.PhoneNumber,
                p.Address AS PropertyAddress
            FROM Tenants t
            JOIN Users u ON t.UserID = u.UserID
            LEFT JOIN Properties p ON t.PropertyID = p.PropertyID
            WHERE 1 = 1
        """
        filters = []

        if property_id:
            query += " AND t.PropertyID = %s"
            filters.append(property_id)
        if rent_status:
            query += " AND t.RentStatus = %s"
            filters.append(rent_status)
        if move_out_requested:
            query += " AND t.MoveOutRequested = %s"
            filters.append(move_out_requested.lower() == "true")

        query += " ORDER BY t.TenantID ASC"

        cursor.execute(query, tuple(filters))
        tenants = cursor.fetchall()

        # Add job history for each tenant
        for tenant in tenants:
            cursor.execute("""
                SELECT JobID, JobType, Description, Status, RequestedTime
                FROM JobRequests
                WHERE TenantID = %s
                ORDER BY RequestedTime DESC
            """, (tenant['TenantID'],))
            tenant['JobHistory'] = cursor.fetchall()

        return jsonify({
            "success": True,
            "filters_applied": {
                "property_id": property_id,
                "rent_status": rent_status,
                "move_out_requested": move_out_requested
            },
            "tenants": tenants
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch tenant data: {str(e)}"
        }), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if tenant exists
        cursor.execute("SELECT * FROM Tenants WHERE TenantID = %s", (tenant_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Tenant not found"}), 404

        # Update move-out request
        cursor.execute("""
            UPDATE Tenants
            SET MoveOutRequested = TRUE
            WHERE TenantID = %s
        """, (tenant_id,))
        conn.commit()

        return jsonify({
            "success": True,
            "message": f"Move-out request submitted for tenant {tenant_id}"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to submit move-out request: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/tenants/<int:tenant_id>/moveout', methods=['PUT'])
def submit_moveout_request(tenant_id):
    data = request.get_json()
    reason = data.get('reason')

    if not reason:
        return jsonify({"success": False, "message": "A reason for the move-out request is required."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if tenant exists
        cursor.execute("SELECT * FROM Tenants WHERE TenantID = %s", (tenant_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Tenant not found"}), 404

        # Update move-out request
        cursor.execute("""
            UPDATE Tenants
            SET MoveOutRequested = TRUE,
                MoveOutReason = %s,
                MoveOutDate = %s
            WHERE TenantID = %s
        """, (reason, datetime.now(), tenant_id))
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Move-out request submitted successfully.",
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to submit move-out request: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/tenants/<int:tenant_id>/rent', methods=['PUT'])
def update_rent_status(tenant_id):
    data = request.get_json()
    rent_status = data.get('rent_status')

    if rent_status not in ['Paid', 'Unpaid']:
        return jsonify({"success": False, "message": "Invalid rent status. Use 'Paid' or 'Unpaid'."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check tenant and fetch old status
        cursor.execute("SELECT RentStatus FROM Tenants WHERE TenantID = %s", (tenant_id,))
        tenant = cursor.fetchone()

        if not tenant:
            return jsonify({"success": False, "message": "Tenant not found"}), 404

        old_status = tenant['RentStatus']
        now = datetime.now()

        # Update tenant rent status and timestamp
        cursor.execute("""
            UPDATE Tenants
            SET RentStatus = %s, RentUpdatedAt = %s
            WHERE TenantID = %s
        """, (rent_status, now, tenant_id))

        # Log the change in audit table
        cursor.execute("""
            INSERT INTO RentAuditLog (TenantID, OldStatus, NewStatus, ChangedAt)
            VALUES (%s, %s, %s, %s)
        """, (tenant_id, old_status, rent_status, now))

        conn.commit()

        return jsonify({
            "success": True,
            "message": f"Rent status updated to '{rent_status}' for tenant {tenant_id}",
            "timestamp": now.isoformat()
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to update rent status: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#OTHER

    data = request.get_json()

    tenant_id = data.get('tenant_id')
    property_id = data.get('property_id')
    job_type = data.get('job_type')
    description = data.get('description')
    urgency = data.get('urgency')  # should be between 1–5

    # Basic validation
    if not all([tenant_id, property_id, job_type, description, urgency]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if not (1 <= int(urgency) <= 5):
        return jsonify({"success": False, "message": "Urgency must be between 1 and 5"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        #verify tenant & property relationship
        cursor.execute("SELECT * FROM Tenants WHERE TenantID = %s AND PropertyID = %s", (tenant_id, property_id))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Tenant not linked to this property"}), 400

        # Insert job request
        cursor.execute("""
            INSERT INTO JobRequests (TenantID, PropertyID, JobType, Description, RequestedTime, Urgency, Status)
            VALUES (%s, %s, %s, %s, NOW(), %s, 'Pending')
        """, (tenant_id, property_id, job_type, description, urgency))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Maintenance request submitted successfully"
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to submit request: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


#JOBREQUEST CALLS
@app.route('/api/jobrequests', methods=['POST'])
def submit_job_request():
    tenant_id = request.form.get('tenant_id')
    property_id = request.form.get('property_id')
    job_type = request.form.get('job_type')
    description = request.form.get('description')
    urgency = request.form.get('urgency')
    file = request.files.get('file')

    if not all([tenant_id, property_id, job_type, description, urgency]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Validate tenant-property relationship
        cursor.execute("SELECT * FROM Tenants WHERE TenantID = %s AND PropertyID = %s", (tenant_id, property_id))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Tenant not linked to this property"}), 400

        # Insert job request
        cursor.execute("""
            INSERT INTO JobRequests (TenantID, PropertyID, JobType, Description, RequestedTime, Urgency, Status)
            VALUES (%s, %s, %s, %s, NOW(), %s, 'Pending')
        """, (tenant_id, property_id, job_type, description, urgency))
        job_id = cursor.lastrowid

        # Handle file upload
        if file:
            filename = secure_filename(file.filename)
            file_data = file.read()
            file_type = file.content_type

            cursor.execute("""
                INSERT INTO JobRequestFiles (JobID, FileName, FileType, FileData)
                VALUES (%s, %s, %s, %s)
            """, (job_id, filename, file_type, file_data))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Maintenance request submitted successfully",
            "job_id": job_id
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to submit request: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/files/<int:file_id>/download', methods=['GET'])
def download_job_file(file_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT FileName, FileType, FileData
            FROM JobRequestFiles
            WHERE FileID = %s
        """, (file_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"success": False, "message": "File not found"}), 404

        filename, filetype, filedata = result

        return Response(
            filedata,
            mimetype=filetype,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to download file: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/jobrequests', methods=['GET'])
def view_all_job_requests():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                j.JobID,
                j.TenantID,
                j.PropertyID,
                j.JobType,
                j.Description,
                j.Urgency,
                j.Status,
                j.RequestedTime,
                u.FirstName AS TenantFirstName,
                u.LastName AS TenantLastName,
                p.Address AS PropertyAddress
            FROM JobRequests j
            JOIN Tenants t ON j.TenantID = t.TenantID
            JOIN Users u ON t.UserID = u.UserID
            JOIN Properties p ON j.PropertyID = p.PropertyID
            ORDER BY j.RequestedTime DESC
        """)

        jobs = cursor.fetchall()

        return jsonify({
            "success": True,
            "job_requests": jobs
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch job requests: {str(e)}"
        }), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/jobrequests/<int:job_id>', methods=['GET'])
def get_job_request_details(job_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get main job info with tenant and property
        cursor.execute("""
            SELECT 
                j.JobID,
                j.TenantID,
                j.PropertyID,
                j.JobType,
                j.Description,
                j.Urgency,
                j.Status,
                j.RequestedTime,
                u.FirstName AS TenantFirstName,
                u.LastName AS TenantLastName,
                u.Email AS TenantEmail,
                u.PhoneNumber AS TenantPhone,
                p.Address AS PropertyAddress
            FROM JobRequests j
            JOIN Tenants t ON j.TenantID = t.TenantID
            JOIN Users u ON t.UserID = u.UserID
            JOIN Properties p ON j.PropertyID = p.PropertyID
            WHERE j.JobID = %s
        """, (job_id,))
        job = cursor.fetchone()

        if not job:
            return jsonify({"success": False, "message": "Job request not found"}), 404

        # Get attached files (if any)
        cursor.execute("""
            SELECT FileID, FileName, FileType, UploadedAt
            FROM JobRequestFiles
            WHERE JobID = %s
        """, (job_id,))
        job["Files"] = cursor.fetchall()

        return jsonify({
            "success": True,
            "job": job
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch job details: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/jobrequests/<int:job_id>/assign', methods=['POST'])
def assign_technician(job_id):
    data = request.get_json()
    technician_id = data.get('technician_id')

    if not technician_id:
        return jsonify({"success": False, "message": "Technician ID is required."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if job exists
        cursor.execute("SELECT * FROM JobRequests WHERE JobID = %s", (job_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Job request not found."}), 404

        # Check if technician exists
        cursor.execute("SELECT * FROM Technicians WHERE TechnicianID = %s", (technician_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Technician not found."}), 404

        # Insert into Assignments
        cursor.execute("""
            INSERT INTO Assignments (TechnicianID, JobID, AssignedTime, Status)
            VALUES (%s, %s, %s, 'Assigned')
        """, (technician_id, job_id, datetime.now()))

        # Optionally update JobRequest status
        cursor.execute("""
            UPDATE JobRequests
            SET Status = 'Assigned'
            WHERE JobID = %s
        """, (job_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": f"Technician {technician_id} assigned to job {job_id}"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to assign technician: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/assignments/<int:assignment_id>', methods=['PATCH'])
def update_assignment(assignment_id):
    data = request.get_json()
    action = data.get('action')  # "start" or "complete"

    if action not in ('start', 'complete'):
        return jsonify({"success": False, "message": "Invalid action. Use 'start' or 'complete'."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if action == 'start':
            cursor.execute("""
                UPDATE Assignments
                SET StartTime = NOW(),
                    Status = 'In Progress'
                WHERE AssignmentID = %s
            """, (assignment_id,))
        else:  # complete
            cursor.execute("""
                UPDATE Assignments
                SET EndTime = NOW(),
                    Status = 'Completed'
                WHERE AssignmentID = %s
            """, (assignment_id,))

        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Assignment not found"}), 404

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Assignment {assignment_id} marked {action}"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to update assignment: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/assignments', methods=['GET'])
def list_assignments():
    tech_id = request.args.get('technician_id')
    job_id = request.args.get('job_id')
    include_completed = request.args.get('include_completed', 'false').lower() == 'true'

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                AssignmentID,
                TechnicianID,
                JobID,
                AssignedTime,
                StartTime,
                EndTime,
                Status
            FROM Assignments
            WHERE 1=1
        """
        params = []

        if tech_id:
            query += " AND TechnicianID = %s"
            params.append(tech_id)
        if job_id:
            query += " AND JobID = %s"
            params.append(job_id)
        if not include_completed:
            query += " AND Status != 'Completed'"

        query += " ORDER BY AssignedTime DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        return jsonify({
            "success": True,
            "filters": {
                "technician_id": tech_id,
                "job_id": job_id,
                "include_completed": include_completed
            },
            "assignments": rows
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to list assignments: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/jobrequests/<int:job_id>/assign', methods=['PUT'])
def reassign_job(job_id):
    data = request.get_json()
    new_tech = data.get('technician_id')
    if not new_tech:
        return jsonify({"success": False, "message": "technician_id is required"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1) Verify job & tech exist
        cursor.execute("SELECT * FROM JobRequests WHERE JobID = %s", (job_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Job not found"}), 404

        cursor.execute("SELECT * FROM Technicians WHERE TechnicianID = %s", (new_tech,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Technician not found"}), 404

        # 2) Cancel any active assignment(s)
        cursor.execute("""
            UPDATE Assignments
            SET Status = 'Cancelled',
                EndTime = %s
            WHERE JobID = %s
              AND Status != 'Completed'
        """, (datetime.now(), job_id))

        # 3) Insert the new assignment record
        cursor.execute("""
            INSERT INTO Assignments (TechnicianID, JobID, AssignedTime, Status)
            VALUES (%s, %s, %s, 'Assigned')
        """, (new_tech, job_id, datetime.now()))

        # 4) Update the JobRequests pointer & status
        cursor.execute("""
            UPDATE JobRequests
            SET AssignedTechnicianID = %s,
                Status = 'Assigned'
            WHERE JobID = %s
        """, (new_tech, job_id))

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Job {job_id} reassigned to technician {new_tech}"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Reassign failed: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



#Ratings calls
@app.route('/api/ratings', methods=['POST'])
def submit_rating():
    data = request.get_json()
    tenant_id     = data.get('tenant_id')
    technician_id = data.get('technician_id')
    job_id        = data.get('job_id')
    rating        = data.get('rating')
    comment       = data.get('comment', '')

    # Validate input
    if not all([tenant_id, technician_id, job_id, rating]):
        return jsonify({"success": False, "message": "tenant_id, technician_id, job_id and rating are required"}), 400
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except ValueError:
        return jsonify({"success": False, "message": "rating must be an integer between 1 and 5"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1) Verify the job exists and matches tenant & technician
        cursor.execute("""
            SELECT AssignedTechnicianID, TenantID
            FROM JobRequests
            WHERE JobID = %s
        """, (job_id,))
        job = cursor.fetchone()
        if not job:
            return jsonify({"success": False, "message": "Job not found"}), 404
        if job['TenantID'] != tenant_id or job['AssignedTechnicianID'] != technician_id:
            return jsonify({"success": False, "message": "Job is not associated with this tenant & technician"}), 400

        # 2) Prevent double‐rating same job
        cursor.execute("""
            SELECT RatingID
            FROM Ratings
            WHERE JobID = %s AND TenantID = %s
        """, (job_id, tenant_id))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "You have already rated this job"}), 409

        # 3) Insert the rating
        cursor.execute("""
            INSERT INTO Ratings (JobID, TechnicianID, TenantID, Rating, Comment, SubmittedTime)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (job_id, technician_id, tenant_id, rating, comment))

        # 4) Recalculate and update technician's average rating
        cursor.execute("""
            SELECT AVG(Rating) AS avg_rating
            FROM Ratings
            WHERE TechnicianID = %s
        """, (technician_id,))
        avg = cursor.fetchone()['avg_rating']

        cursor.execute("""
            UPDATE Technicians
            SET AvgRating = %s
            WHERE TechnicianID = %s
        """, (avg, technician_id))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Rating submitted successfully",
            "avg_rating": round(avg, 2)
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to submit rating: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/technicians/<int:technician_id>/rating', methods=['GET'])
def get_technician_rating(technician_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Compute average and count of ratings
        cursor.execute("""
            SELECT 
                AVG(Rating)   AS avg_rating,
                COUNT(*)      AS rating_count
            FROM Ratings
            WHERE TechnicianID = %s
        """, (technician_id,))
        result = cursor.fetchone()

        avg = result['avg_rating']
        count = result['rating_count']

        # If no ratings yet, avg will be None
        return jsonify({
            "success": True,
            "technician_id": technician_id,
            "rating_count": count,
            "avg_rating": avg is not None and round(avg, 2) or None
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch rating: {str(e)}"
        }), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



#INVOICES
@app.route('/api/invoices', methods=['POST'])
def submit_invoice():
    data = request.get_json()
    technician_id = data.get('technician_id')
    job_id        = data.get('job_id')
    amount        = data.get('amount')

    # Basic validation
    if not all([technician_id, job_id, amount]):
        return jsonify({"success": False, "message": "technician_id, job_id, and amount are required"}), 400

    try:
        # ensure amount is a positive number
        amt = float(amount)
        if amt <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"success": False, "message": "amount must be a positive number"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # verify technician exists
        cursor.execute("SELECT TechnicianID FROM Technicians WHERE TechnicianID = %s", (technician_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Technician not found"}), 404

        # verify job exists and was assigned to this technician
        cursor.execute("""
            SELECT AssignedTechnicianID 
            FROM JobRequests 
            WHERE JobID = %s
        """, (job_id,))
        job = cursor.fetchone()
        if not job:
            return jsonify({"success": False, "message": "Job request not found"}), 404
        if job[0] != technician_id:
            return jsonify({"success": False, "message": "Technician not assigned to this job"}), 400

        # insert invoice
        cursor.execute("""
            INSERT INTO Invoices (TechnicianID, JobID, Amount)
            VALUES (%s, %s, %s)
        """, (technician_id, job_id, amt))
        invoice_id = cursor.lastrowid

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Invoice submitted successfully",
            "invoice": {
                "InvoiceID": invoice_id,
                "TechnicianID": technician_id,
                "JobID": job_id,
                "Amount": amt,
                "Status": "Unpaid"
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to submit invoice: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/invoices/<int:invoice_id>/status', methods=['PUT'])
def update_invoice_status(invoice_id):
    data = request.get_json()
    status = data.get('status')
    if status not in ('Paid', 'Unpaid'):
        return jsonify({"success": False, "message": "Invalid status; use 'Paid' or 'Unpaid'."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # check exists
        cursor.execute("SELECT * FROM Invoices WHERE InvoiceID = %s", (invoice_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Invoice not found"}), 404

        cursor.execute(
            "UPDATE Invoices SET Status = %s WHERE InvoiceID = %s",
            (status, invoice_id)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": f"Invoice {invoice_id} marked '{status}'"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to update invoice: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/invoices', methods=['GET'])
def list_invoices():
    tech_id = request.args.get('technician_id')
    job_id  = request.args.get('job_id')

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT InvoiceID, TechnicianID, JobID, Amount, SentTime, Status
            FROM Invoices
            WHERE 1=1
        """
        params = []
        if tech_id:
            query += " AND TechnicianID = %s"
            params.append(tech_id)
        if job_id:
            query += " AND JobID = %s"
            params.append(job_id)
        query += " ORDER BY SentTime DESC"

        cursor.execute(query, tuple(params))
        invoices = cursor.fetchall()

        return jsonify({
            "success": True,
            "filters": {
                "technician_id": tech_id,
                "job_id": job_id
            },
            "invoices": invoices
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch invoices: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == '__main__':
    app.run(debug=True ,host = '0.0.0.0', port = 5150)
