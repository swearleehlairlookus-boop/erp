#!/usr/bin/env python3
"""
Check Database Tables for Dashboard
"""

import mysql.connector
from database import get_db_connection

def check_tables():
    """Check what tables exist in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("=== DATABASE TABLES ===")
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            # Get table structure
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            print("   Columns:")
            for col in columns:
                print(f"     - {col[0]} ({col[1]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   Rows: {count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tables()