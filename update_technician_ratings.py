import mysql.connector

def update_technician_ratings():
    connection = mysql.connector.connect(
        host="localhost",
        user="Peter",
        password="",
        database="DPM"
    )
    cursor = connection.cursor()

    cursor.execute("""
        SELECT TechnicianID, AVG(Rating) AS AvgRating
        FROM MaintenanceRequests
        WHERE Status = 'Completed' AND Rating IS NOT NULL
        GROUP BY TechnicianID
    """)
    rating_updates = cursor.fetchall()

    for technician_id, avg_rating in rating_updates:
        cursor.execute("""
            UPDATE Technicians
            SET Rating = %s
            WHERE TechnicianID = %s
        """, (round(avg_rating, 2), technician_id))

    connection.commit()
    cursor.close()
    connection.close()
    print("✅ Technician ratings updated based on completed maintenance requests.")

if __name__ == "__main__":
    update_technician_ratings()
