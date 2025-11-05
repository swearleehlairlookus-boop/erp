
import mysql.connector
import os

# Use the same DB credentials as create_admin_user.py
DB_HOST = os.environ.get('DB_HOST', 'db-polmed.mysql.database.azure.com')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_NAME = os.environ.get('DB_NAME', 'mobile_clinic_erp')
DB_USER = os.environ.get('DB_USER', 'dbadmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Polm3d!DB@2025')

DB_CONFIG = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
    'port': DB_PORT,
}

def check_asset_status(asset_name):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT asset_name, status FROM assets WHERE asset_name = %s", (asset_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        print(f"Asset: {result[0]}, Status: {result[1]}")
    else:
        print("Asset not found.")

if __name__ == "__main__":
    check_asset_status("Digital Blood Pressure Monitor")
