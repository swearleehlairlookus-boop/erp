"""
POLMED Backend - Database Connection Module
Singleton pattern for MySQL database connections
"""

import mysql.connector
from mysql.connector import Error
import os
from contextlib import contextmanager

class Database:
    """Database connection singleton"""
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    @staticmethod
    def get_connection():
        """Get or create database connection"""
        try:
            connection = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'db-polmed.mysql.database.azure.com'),
                port=int(os.environ.get('DB_PORT', 3306)),
                user=os.environ.get('DB_USER', 'dbadmin'),
                password=os.environ.get('DB_PASSWORD', 'Polm3d!DB@2025'),
                database=os.environ.get('DB_NAME', 'mobile_clinic_erp'),
                autocommit=False,
                use_unicode=True,
                charset='utf8mb4',
                ssl_disabled=False,
                ssl_verify_cert=False,
                ssl_verify_identity=False
            )
            return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None

def get_db_connection():
    """Get database connection (helper function)"""
    return Database.get_connection()

def close_db_connection(connection):
    """Close database connection"""
    if connection and connection.is_connected():
        connection.close()

@contextmanager
def database_session():
    """Context manager for database sessions"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        close_db_connection(conn)
