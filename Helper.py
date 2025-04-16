#Author: Zedaine McDonald
from flask import Flask, jsonify, request
import mysql.connector
from typing import Dict
import re
from email_validator import validate_email, EmailNotValidError
import string, random

def get_connection():
    try:
        return mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "Configure1738",
            database = "dpm2")

        cursor = db.cursor(dictionary = True)
    except mysql.connector.Error as err:
        print (f'Error:{err}')
        
def is_valid_email(email):
    try:
        valid = validate_email(email)
        return valid.email  # Returns normalized email
    except EmailNotValidError:
        return False
    
# Random password generator
def generate_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
