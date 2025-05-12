import mysql.connector

db_connection = mysql.connector.connect(
    host="localhost",
    user="Peter",
    password="12345",
    database="ShopDB"
)

def fetch_data():
    cursor = db_connection.cursor(dictionary=True)
    

    cursor.execute("SELECT * FROM Technicians")
    technicians = cursor.fetchall()
    

    cursor.execute("SELECT * FROM Properties")
    properties = cursor.fetchall()

    maintenance_request = {
        "SkillsetRequired": "Plumbing", 
        "Rating": 4,  
        "PropertyZone": "Uptown",  
        "Urgency": 2 
    }
    
    return technicians, properties, maintenance_request

def calculate_score(technician, request):
    skillset_match = 1 if technician["Skillset"] == request["SkillsetRequired"] else 0
    
    rating = request["Rating"] / 5
    
    zone_match = 1 if technician["Zone"] == request["PropertyZone"] else 0
    
    if technician["Status"] == "Busy":
        urgency_score = 0
    else:
        urgency_score = request["Urgency"] / 3
    
    score = (skillset_match * 0.25) + (rating * 0.25) + (zone_match * 0.30) + (urgency_score * 0.20)
    
    return score

def assign_technician(technicians, maintenance_request):
    technician_scores = []
    for technician in technicians:
        score = calculate_score(technician, maintenance_request)
        technician_scores.append({"Technician": technician, "Score": score})
    
    technician_scores.sort(key=lambda x: x["Score"], reverse=True)
    
    highest_score = technician_scores[0]["Score"]
    
    top_technicians = [tech for tech in technician_scores if tech["Score"] == highest_score]
    
    selected_technician = top_technicians[0]["Technician"]
    
    return selected_technician
