import sqlite3

db_path = r"c:\Users\bipan\Desktop\projects\attendace tracker\backend\db.sqlite3"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("Creating DeviceFingerprint table...")
    print("=" * 60)
    
    # Create the DeviceFingerprint table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mysite_devicefingerprint (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_hash VARCHAR(128) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            course_id BIGINT NOT NULL,
            session_id BIGINT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES mysite_course(id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES mysite_attendancesession(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
            UNIQUE (user_id, course_id, session_id)
        );
    """)
    print("✓ Created mysite_devicefingerprint table")
    
    # Now mark the migration as applied in django_migrations table
    print("\n" + "=" * 60)
    print("Marking migration 0011 as applied...")
    print("=" * 60)
    
    try:
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('mysite', '0011_attendance_student_latitude_and_more', CURRENT_TIMESTAMP)
        """)
        print("✓ Migration 0011 marked as applied")
    except sqlite3.IntegrityError:
        print("✓ Migration 0011 already marked as applied")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database migration completed!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
