#!/usr/bin/env python3
print("Starting schema update...")

import pymysql
import sys

try:
    print("Connecting to MySQL database...")
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='billsmart_db'
    )
    print("✓ Connected successfully")
    
    cursor = connection.cursor()
    
    # Check current table structure first
    print("\nCurrent products table structure:")
    cursor.execute("DESCRIBE products;")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]} - {col[1]}")
    
    # Add missing columns to products table
    alter_queries = [
        "ALTER TABLE products ADD COLUMN cost_price DECIMAL(10,2) AFTER stock_quantity;",
        "ALTER TABLE products ADD COLUMN min_stock_level INTEGER DEFAULT 0 AFTER cost_price;", 
        "ALTER TABLE products ADD COLUMN sku VARCHAR(100) AFTER min_stock_level;"
    ]
    
    print("\nExecuting ALTER TABLE queries...")
    for query in alter_queries:
        try:
            cursor.execute(query)
            print(f"✓ Executed: {query}")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print(f"⚠ Column already exists: {query}")
            else:
                print(f"✗ Error: {e}")
    
    connection.commit()
    print("✓ Changes committed")
    
    # Verify the changes
    print("\nUpdated products table structure:")
    cursor.execute("DESCRIBE products;")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]} - {col[1]}")
    
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
finally:
    if 'connection' in locals():
        connection.close()
        print("✓ Database connection closed")

print("Schema update complete!")
