import mysql.connector
from mysql.connector import Error
import urllib.parse

def create_database():
    try:
        # Get the correct password (URL decoded)
        password = urllib.parse.unquote('Devil%4006')
        
        # Connect to MySQL server
        print("Connecting to MySQL...")
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create the database
            print("Creating hospital_db database...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS hospital_db")
            
            # Use the database
            cursor.execute("USE hospital_db")
            
            # Set character set and collation
            cursor.execute("ALTER DATABASE hospital_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            print("Database hospital_db created successfully!")
            
            # Close the connection
            cursor.close()
            connection.close()
            print("MySQL connection closed.")
            
            return True
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return False

if __name__ == "__main__":
    create_database() 