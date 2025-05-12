import mysql.connector
from Technician_Assignment.technician import Technician

def load_technicians_from_db():
    connection = mysql.connector.connect(
        host="localhost",
        database="DPM",
        user="root",
        password="password"
    )

    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.TechnicianID, CONCAT(u.FirstName, ' ', u.LastName) AS name, 
               t.Skillset, t.Status, u.UserID, u.Email, t.Zone
        FROM Technicians t
        JOIN Users u ON t.UserID = u.UserID
    """)

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    technicians = []
    for row in rows:
        technicians.append(Technician(
            id=row["TechnicianID"],
            name=row["name"],
            skillset=row["Skillset"],
            zone=row["Zone"],
            status=row["Status"]
        ))

    return technicians
