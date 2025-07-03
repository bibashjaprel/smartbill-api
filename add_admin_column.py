"""
Script to add is_admin column to existing users table
Run this if you have an existing database
"""
import mysql.connector
from app.core.config import settings

def add_admin_column():
    try:
        # Parse DATABASE_URL to get connection details
        db_url = settings.DATABASE_URL
        # Remove mysql+pymysql:// prefix
        db_url = db_url.replace("mysql+pymysql://", "")
        
        # Extract user:password@host:port/database
        user_pass, host_db = db_url.split("@")
        
        # Handle empty password case
        if ":" in user_pass:
            user, password = user_pass.split(":", 1)
        else:
            user = user_pass
            password = ""
            
        host_port, database = host_db.split("/")
        
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 3306
        
        # Connect to database
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        # Check if is_admin column exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'users'
            AND COLUMN_NAME = 'is_admin'
        """, (database,))
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            # Add is_admin column
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN is_admin BOOLEAN DEFAULT false AFTER is_verified
            """)
            print("✅ Added is_admin column to users table")
            
            # Ask if we want to create a default admin user
            create_admin = input("Do you want to create a default admin user? (y/n): ").lower().strip()
            if create_admin == 'y':
                admin_email = input("Enter admin email: ").strip()
                if admin_email:
                    cursor.execute("""
                        UPDATE users 
                        SET is_admin = true 
                        WHERE email = %s
                    """, (admin_email,))
                    
                    if cursor.rowcount > 0:
                        print(f"✅ User {admin_email} has been made an admin")
                    else:
                        print(f"❌ User {admin_email} not found in database")
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
