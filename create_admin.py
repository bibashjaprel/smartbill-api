#!/usr/bin/env python3
import pymysql
import uuid
from datetime import datetime
import bcrypt

try:
    # Connect to database
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='billsmart_db'
    )
    cursor = connection.cursor()
    
    # Check if admin user exists
    cursor.execute("SELECT * FROM users WHERE email = 'admin@example.com';")
    existing_user = cursor.fetchone()
    
    if existing_user:
        print("Admin user already exists:")
        print(f"  ID: {existing_user[0]}")
        print(f"  Email: {existing_user[1]}")
        print(f"  Is Admin: {existing_user[6]}")
    else:
        # Create admin user
        user_id = str(uuid.uuid4())
        email = 'admin@example.com'
        password = 'admin123'
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, email, password_hash, 'Admin User', True, True, True))
        
        connection.commit()
        print("✓ Admin user created successfully")
        
        # Create a shop for the admin user
        shop_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO shops (id, name, owner_id)
            VALUES (%s, %s, %s)
        """, (shop_id, 'Admin Shop', user_id))
        
        connection.commit()
        print("✓ Admin shop created successfully")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'connection' in locals():
        connection.close()
