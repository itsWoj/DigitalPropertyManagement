#recommend_tech.py

import mysql.connector
from collections import defaultdict
from tabulate import tabulate

# Connect to DB
conn = mysql.connector.connect(
    host="localhost",
    user="Peter",
    password="18760",
    database="DPM"
)
cursor = conn.cursor(dictionary=True)

job_types = ['Plumbing', 'Electrical', 'HVAC', 'Electric', 'General']

# Get technicians
cursor.execute("SELECT * FROM Technicians")
technicians = cursor.fetchall()
tech_zones = {t['TechnicianID']: t['Zone'] for t in technicians}
tech_skills = {t['TechnicianID']: t['Skillset'] for t in technicians}

# Get ratings
cursor.execute("""
    SELECT t.TechnicianID, r.Rating, j.JobType, p.Zone, j.Urgency
    FROM Ratings r
    JOIN JobRequests j ON r.JobID = j.JobID
    JOIN Properties p ON j.PropertyID = p.PropertyID
    JOIN Technicians t ON t.TechnicianID = r.TechnicianID
""")
ratings_data = cursor.fetchall()

# Rating matrix
rating_matrix = defaultdict(list)
urgency_matrix = defaultdict(list)
zone_skill_rating = defaultdict(list)

for row in ratings_data:
    key = (row['TechnicianID'], row['JobType'])
    rating_matrix[key].append(row['Rating'])
    urgency_matrix[key].append(row['Urgency'])
    zone_skill_rating[(row['Zone'], row['JobType'])].append(row['Rating'])

# Zone/skill averages
avg_zone_skill_rating = {
    k: round(sum(v) / len(v), 2)
    for k, v in zone_skill_rating.items() if v
}

# Estimate rating
def estimate_rating(tech_id, job_type):
    zone = tech_zones.get(tech_id)
    return avg_zone_skill_rating.get((zone, job_type), 3.0)

# Average urgency by job_type
job_type_urgency = defaultdict(list)
for row in ratings_data:
    job_type_urgency[row['JobType']].append(row['Urgency'])

avg_urgency = {
    jt: sum(v)/len(v) for jt, v in job_type_urgency.items()
}

# Compute scores
scores = []
for tech in technicians:
    tech_id = tech['TechnicianID']
    zone = tech['Zone']
    skillset = tech['Skillset']

    for job_type in job_types:
        skillset_score = 25 if skillset == job_type else 12.5
        zone_score = 30 if zone in ['Uptown', 'Downtown', 'Crossroad', 'Zone A', 'BackRoad'] else 15

        ratings = rating_matrix.get((tech_id, job_type), [])
        rating_score = (sum(ratings)/len(ratings) if ratings else estimate_rating(tech_id, job_type)) / 5 * 25

        urgency = avg_urgency.get(job_type, 3)
        if urgency >= 4:
            urgency_score = 20 if tech_zones.get(tech_id) == zone else 0
        else:
            urgency_score = 10 if tech_zones.get(tech_id) == zone else 0

        score = round(skillset_score + rating_score + zone_score + urgency_score, 2)
        scores.append((tech_id, job_type, score))

# Save to DB
cursor.execute("DELETE FROM Precomputed_MF_Scores")
for tech_id, job_type, mf_score in scores:
    cursor.execute("""
        INSERT INTO Precomputed_MF_Scores (TechnicianID, JobType, MF_Score)
        VALUES (%s, %s, %s)
    """, (tech_id, job_type, mf_score))

conn.commit()

# Table display
matrix = defaultdict(dict)
for tech_id, job_type, score in scores:
    matrix[job_type][tech_id] = score

tech_ids = sorted(tech_zones.keys())
headers = ["JobType"] + [str(tid) for tid in tech_ids]
rows = []

for job_type in job_types:
    row = [job_type]
    for tid in tech_ids:
        row.append(matrix[job_type].get(tid, '-'))
    rows.append(row)

print(f"Number of scores: {len(scores)}")
print("Sample scores:", scores[:5])
print(tabulate(rows, headers=headers, tablefmt="pretty"))

cursor.close()
conn.close()
