import mysql.connector
import re

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        database="DPM",
        user="root",
        password="18760"
    )

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def generate_password():
    import random, string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))
