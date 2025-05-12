import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="Peter",
        password="18760",
        database="DPM"
    )