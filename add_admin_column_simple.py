"""
Simple script to add is_admin column to users table
"""
import mysql.connector
from app.core.config import settings

def add_admin_column():
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='billsmart_db'
        )
        
        cursor = connection.cursor()
        
        # Check if is_admin column exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'billsmart_db'
            AND TABLE_NAME = 'users'
            AND COLUMN_NAME = 'is_admin'
        """)
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            # Add is_admin column
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN is_admin BOOLEAN DEFAULT false AFTER is_verified
            """)
            print("✅ Added is_admin column to users table")
        else:
            print("ℹ️  is_admin column already exists")
        
        connection.commit()
        
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ Database connection closed")

if __name__ == "__main__":
    add_admin_column()
