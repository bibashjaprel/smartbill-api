import pymysql
import sys

def update_database_schema():
    """Update database schema to add new columns for email verification and Google OAuth"""
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='billsmart_db',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Check if new columns exist, if not add them
            cursor.execute("SHOW COLUMNS FROM users LIKE 'is_verified'")
            if not cursor.fetchone():
                print("Adding is_verified column...")
                cursor.execute("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT false")
                
            cursor.execute("SHOW COLUMNS FROM users LIKE 'google_id'")
            if not cursor.fetchone():
                print("Adding google_id column...")
                cursor.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR(255) UNIQUE")
                
            cursor.execute("SHOW COLUMNS FROM users LIKE 'profile_picture'")
            if not cursor.fetchone():
                print("Adding profile_picture column...")
                cursor.execute("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(500)")
                
            # Make password_hash nullable for Google OAuth users
            cursor.execute("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NULL")
            
            # Add index on google_id if it doesn't exist
            cursor.execute("SHOW INDEX FROM users WHERE Key_name = 'google_id'")
            if not cursor.fetchone():
                print("Adding index on google_id...")
                cursor.execute("CREATE INDEX idx_google_id ON users(google_id)")
        
        connection.commit()
        print("Database schema updated successfully!")
        
    except pymysql.Error as e:
        print(f"Error updating database schema: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    update_database_schema()
