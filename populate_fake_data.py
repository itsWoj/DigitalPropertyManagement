import mysql.connector
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'Peter',
    'password': '18760',
    'database': 'DPM'
}

# Constants matching database ENUMs
SKILLSETS = ['Plumbing', 'Electrical', 'HVAC', 'Electric']  # Now includes 'Electric'
ZONES = ['Uptown', 'Downtown', 'Crossroad', 'Zone A', 'BackRoad']
STATUSES = ['Pending', 'InProgress', 'Completed']
RENT_STATUSES = ['Paid', 'Due', 'Overdue']

# Population counts
NUM_TENANTS = 10
NUM_MANAGERS = 5
NUM_TECHNICIANS = 8
NUM_PROPERTIES = 15
NUM_REQUESTS = 20

def generate_id(prefix, index):
    """Generate consistent IDs with prefix and 3-digit number"""
    return f"{prefix}{100 + index:03d}"

def create_users(conn):
    """Create all user accounts with proper roles"""
    print("👥 Creating users...")
    cursor = conn.cursor(dictionary=True)
    user_ids = []
    
    try:
        # Create Tenants
        for i in range(NUM_TENANTS):
            user_id = generate_id('TEN', i)
            cursor.execute("""
                INSERT INTO Users (UserID, Email, PasswordHash, Role, FirstName, LastName)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                fake.unique.email(),
                fake.password(),
                'Tenant',
                fake.first_name(),
                fake.last_name()
            ))
            user_ids.append(user_id)
        
        # Create Managers
        for i in range(NUM_MANAGERS):
            user_id = generate_id('MAN', i)
            cursor.execute("""
                INSERT INTO Users (UserID, Email, PasswordHash, Role, FirstName, LastName)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                fake.unique.email(),
                fake.password(),
                'Manager',
                fake.first_name(),
                fake.last_name()
            ))
            user_ids.append(user_id)
        
        # Create Technicians
        for i in range(NUM_TECHNICIANS):
            user_id = generate_id('TECH', i)
            cursor.execute("""
                INSERT INTO Users (UserID, Email, PasswordHash, Role, FirstName, LastName)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                fake.unique.email(),
                fake.password(),
                'Technician',
                fake.first_name(),
                fake.last_name()
            ))
            user_ids.append(user_id)
        
        conn.commit()
        print(f"✅ Created {len(user_ids)} users")
        return user_ids
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating users: {e}")
        raise
    finally:
        cursor.close()

def create_properties(conn, manager_ids):
    """Create properties with random managers"""
    print("🏠 Creating properties...")
    cursor = conn.cursor(dictionary=True)
    property_ids = []
    
    try:
        for i in range(NUM_PROPERTIES):
            prop_id = generate_id('PROP', i)
            cursor.execute("""
                INSERT INTO Properties (PropertyID, Address, Zone, ManagerID, Status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                prop_id,
                fake.address().replace('\n', ', '),
                random.choice(ZONES),
                random.choice(manager_ids),
                'Active'
            ))
            property_ids.append(prop_id)
        
        conn.commit()
        print(f"✅ Created {len(property_ids)} properties")
        return property_ids
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating properties: {e}")
        raise
    finally:
        cursor.close()

def create_tenants(conn, tenant_user_ids, property_ids):
    """Create tenant records with optional property assignment"""
    print("👨‍👩‍👧‍👦 Creating tenants...")
    cursor = conn.cursor(dictionary=True)
    
    try:
        for i, user_id in enumerate(tenant_user_ids):
            tenant_id = generate_id('TEN', i)
            prop_id = random.choice(property_ids) if random.random() > 0.3 else None
            
            cursor.execute("""
                INSERT INTO Tenants (TenantID, UserID, PropertyID, RentStatus, RentUpdatedAt)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                tenant_id,
                user_id,
                prop_id,
                random.choice(RENT_STATUSES),
                fake.date_time_this_year()
            ))
        
        conn.commit()
        print(f"✅ Created {len(tenant_user_ids)} tenants")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating tenants: {e}")
        raise
    finally:
        cursor.close()

def create_technicians(conn, tech_user_ids):
    """Create technician records with random skills and ratings"""
    print("🔧 Creating technicians...")
    cursor = conn.cursor(dictionary=True)
    
    try:
        for i, user_id in enumerate(tech_user_ids):
            tech_id = generate_id('TECH', i)
            cursor.execute("""
                INSERT INTO Technicians (TechnicianID, UserID, Skillset, Status, Zone, Rating)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                tech_id,
                user_id,
                random.choice(SKILLSETS),
                random.choice(['Free', 'Busy']),
                random.choice(ZONES),
                round(random.uniform(3.0, 5.0), 1)  # Rating between 3.0-5.0
            ))
            print(f"  Added technician {tech_id}")
        
        conn.commit()
        print(f"✅ Created {len(tech_user_ids)} technicians")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating technicians: {e}")
        raise
    finally:
        cursor.close()

def create_maintenance_requests(conn, tenant_ids):
    """Create maintenance requests with realistic data"""
    print("🛠️ Creating maintenance requests...")
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all technician IDs
        cursor.execute("SELECT TechnicianID FROM Technicians")
        all_tech_ids = [t['TechnicianID'] for t in cursor.fetchall()]
        
        for _ in range(NUM_REQUESTS):
            tenant_id = random.choice(tenant_ids)
            created_at = fake.date_time_this_year()
            
            # Randomly decide if completed
            is_completed = random.random() > 0.5
            status = 'Completed' if is_completed else random.choice(['Pending', 'InProgress'])
            completed_at = created_at + timedelta(days=random.randint(1, 7)) if is_completed else None
            tech_id = random.choice(all_tech_ids) if is_completed else None
            rating = random.randint(3, 5) if is_completed else None
            
            cursor.execute("""
                INSERT INTO MaintenanceRequests (
                    TenantID, TechnicianID, Skillset, Description, Zone, 
                    Urgency, Status, Rating, CreatedAt, CompletedAt
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tenant_id,
                tech_id,
                random.choice(SKILLSETS),
                fake.sentence(),
                random.choice(ZONES),
                random.randint(1, 3),
                status,
                rating,
                created_at,
                completed_at
            ))
        
        conn.commit()
        print(f"✅ Created {NUM_REQUESTS} maintenance requests")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating maintenance requests: {e}")
        raise
    finally:
        cursor.close()

def main():
    """Main function to populate the database"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("🔌 Connected to database")
        
        # Create all entities
        user_ids = create_users(conn)
        tenant_ids = [uid for uid in user_ids if uid.startswith('TEN')]
        manager_ids = [uid for uid in user_ids if uid.startswith('MAN')]
        tech_ids = [uid for uid in user_ids if uid.startswith('TECH')]
        
        property_ids = create_properties(conn, manager_ids)
        create_tenants(conn, tenant_ids, property_ids)
        create_technicians(conn, tech_ids)
        create_maintenance_requests(conn, tenant_ids)
        
        print("\n✅ Database successfully populated with fake data!")
        
    except Exception as e:
        print(f"\n❌ Error during database population: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    main()