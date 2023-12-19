import mysql.connector
import os


def create_db_connection():
    try:
        db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "database": os.getenv("DATABASE_NAME"),
        }
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise
