import random
from faker import Faker
import mysql.connector

fake = Faker()

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="Peter",
    password="18760",  # Replace if needed
    database="DPM"
)
cur = conn.cursor()

# ----- CONFIGURATION -----
ZONES = ['Uptown', 'Downtown', 'Crossroad', 'Zone A', 'BackRoad']
SKILLSETS = ['Plumbing', 'Electrical', 'HVAC', 'Electric']
ROLES = ['Admin', 'Technician', 'Tenant', 'Manager']

# ----- USERS -----
def create_users(count, role, prefix="USER"):
    users = []
    existing_ids = set()
    cur.execute("SELECT UserID FROM Users WHERE Role = %s", (role,))
    existing_ids.update(row[0] for row in cur.fetchall())  # Fetch existing UserIDs for this role
    
    for i in range(count):
        user_id = f"{prefix}{i+1:04d}"  # e.g., USER0001
        # Check if UserID exists, and if so, increment until unique
        while user_id in existing_ids:
            i += 1
            user_id = f"{prefix}{i+1:04d}"
        existing_ids.add(user_id)  # Add to the set of existing UserIDs
        
        users.append((user_id, fake.email(), fake.sha256(), role, fake.first_name(), fake.last_name()))
    
    cur.executemany("""
        INSERT INTO Users (UserID, Email, PasswordHash, Role, FirstName, LastName)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, users)
    conn.commit()
    return [user[0] for user in users]

# ----- MANAGERS -----
manager_user_ids = create_users(5, 'Manager', prefix="MAN")

# ----- PROPERTIES -----
def create_properties(count, manager_user_ids):
    properties = []
    for i in range(count):
        property_id = f"PROP{i+1:03d}"
        address = fake.address().replace("\n", ", ")
        zone = random.choice(ZONES)
        manager_id = random.choice(manager_user_ids)
        properties.append((property_id, address, zone, manager_id))
    cur.executemany("""
        INSERT INTO Properties (PropertyID, Address, Zone, ManagerID)
        VALUES (%s, %s, %s, %s)
    """, properties)
    conn.commit()
    cur.execute("SELECT PropertyID FROM Properties")
    return [row[0] for row in cur.fetchall()]

property_ids = create_properties(15, manager_user_ids)

# ----- TENANTS -----
tenant_user_ids = create_users(10, 'Tenant', prefix="TEN")
tenants = []
for i, uid in enumerate(tenant_user_ids):
    tenant_id = f"TEN{i+1:03d}"
    property_id = random.choice(property_ids)
    tenants.append((tenant_id, uid, property_id))
cur.executemany("""
    INSERT INTO Tenants (TenantID, UserID, PropertyID)
    VALUES (%s, %s, %s)
""", tenants)
conn.commit()

# ----- TECHNICIANS -----
technician_user_ids = create_users(8, 'Technician', prefix="TECH")
technicians = []
for i, uid in enumerate(technician_user_ids):
    technician_id = f"TECH{i+1:03d}"
    skillset = random.choice(SKILLSETS)
    zone = random.choice(ZONES)
    rating = round(random.uniform(2.5, 5.0), 2)
    technicians.append((technician_id, uid, skillset, zone, rating))
cur.executemany("""
    INSERT INTO Technicians (TechnicianID, UserID, Skillset, Zone, AvgRating)
    VALUES (%s, %s, %s, %s, %s)
""", technicians)
conn.commit()

# ----- JOB REQUESTS -----
cur.execute("SELECT TenantID FROM Tenants")
tenant_ids = [row[0] for row in cur.fetchall()]
job_types = SKILLSETS + ['General']
job_requests = []
for i in range(20):
    tenant_id = random.choice(tenant_ids)
    property_id = random.choice(property_ids)
    job_type = random.choice(job_types)
    desc = fake.sentence()
    urgency = random.randint(1, 5)
    job_id = f"JOB{i+1:02d}"  # Format JobID as JOBXX
    job_requests.append((job_id, tenant_id, property_id, job_type, desc, urgency))

try:
    cur.executemany("""
        INSERT INTO JobRequests (JobID, TenantID, PropertyID, JobType, Description, Urgency)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, job_requests)
    conn.commit()
    print("✔ Fake data inserted successfully.")
except mysql.connector.Error as err:
    print(f"Error: {err}")

cur.close()
conn.close()
