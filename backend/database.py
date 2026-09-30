import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin123",
        database="Cloud_Hospital_Appointment"
    )

    return connection