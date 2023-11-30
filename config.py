import configparser
import mysql.connector


def load_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config


def get_upload_folder():
    config = load_config()
    return config["Paths"]["upload_folder"]


def get_database_config():
    config = load_config()
    return {
        "host": config["Database"]["host"],
        "user": config["Database"]["user"],
        "password": config["Database"]["password"],
        "database": config["Database"]["database"],
    }


def create_db_connection():
    db_config = get_database_config()
    connection = mysql.connector.connect(**db_config)
    return connection

