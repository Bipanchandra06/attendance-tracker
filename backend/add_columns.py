import sqlite3
import os

db_path = r"c:\Users\bipan\Desktop\projects\attendace tracker\backend\db.sqlite3"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("Checking mysite_attendancesession table structure...")
    print("=" * 60)
    cursor.execute("PRAGMA table_info(mysite_attendancesession);")
    columns = cursor.fetchall()
    for col in columns:
        print(f"Column: {col[1]}, Type: {col[2]}")
    
    print("\n" + "=" * 60)
    print("Adding missing columns if needed...")
    print("=" * 60)
    
    # Add latitude column if not exists
    try:
        cursor.execute("ALTER TABLE mysite_attendancesession ADD COLUMN latitude DECIMAL(9,6) NULL;")
        print("✓ Added latitude column")
    except sqlite3.OperationalError as e:
        print(f"✗ latitude column: {e}")
    
    # Add longitude column if not exists
    try:
        cursor.execute("ALTER TABLE mysite_attendancesession ADD COLUMN longitude DECIMAL(9,6) NULL;")
        print("✓ Added longitude column")
    except sqlite3.OperationalError as e:
        print(f"✗ longitude column: {e}")
    
    # Add radius_meters column if not exists
    try:
        cursor.execute("ALTER TABLE mysite_attendancesession ADD COLUMN radius_meters INTEGER DEFAULT 100 NULL;")
        print("✓ Added radius_meters column")
    except sqlite3.OperationalError as e:
        print(f"✗ radius_meters column: {e}")
    
    # Add to attendance table too
    print("\n" + "=" * 60)
    print("Checking mysite_attendance table structure...")
    print("=" * 60)
    cursor.execute("PRAGMA table_info(mysite_attendance);")
    columns = cursor.fetchall()
    for col in columns:
        print(f"Column: {col[1]}, Type: {col[2]}")
    
    print("\n" + "=" * 60)
    print("Adding missing columns to attendance if needed...")
    print("=" * 60)
    
    try:
        cursor.execute("ALTER TABLE mysite_attendance ADD COLUMN student_latitude DECIMAL(9,6) NULL;")
        print("✓ Added student_latitude column")
    except sqlite3.OperationalError as e:
        print(f"✗ student_latitude column: {e}")
    
    try:
        cursor.execute("ALTER TABLE mysite_attendance ADD COLUMN student_longitude DECIMAL(9,6) NULL;")
        print("✓ Added student_longitude column")
    except sqlite3.OperationalError as e:
        print(f"✗ student_longitude column: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database update completed!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
