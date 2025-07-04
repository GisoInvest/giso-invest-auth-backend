#!/usr/bin/env python3
"""
Database Migration Script for GISO Invest Backend
Adds new subscription-related columns to existing user table
"""

import sqlite3
import os
from datetime import datetime, timedelta

def migrate_database():
    """Add missing columns to the user table"""
    
    # Database path
    db_path = 'src/database/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    print("🔄 Starting database migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current table schema
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Existing columns: {existing_columns}")
        
        # Define new columns to add
        new_columns = [
            ("trial_active", "BOOLEAN DEFAULT 1"),
            ("subscription_plan", "VARCHAR(20) DEFAULT 'trial'"),
            ("subscription_status", "VARCHAR(50) DEFAULT 'trial_active'"),
            ("plan", "VARCHAR(50) DEFAULT 'trial'"),
            ("subscription_start_date", "DATETIME"),
            ("last_payment_date", "DATETIME"),
            ("next_billing_date", "DATETIME"),
            ("payment_required", "BOOLEAN DEFAULT 0"),
            ("stripe_customer_id", "VARCHAR(255)"),
            ("stripe_payment_intent_id", "VARCHAR(255)"),
            ("last_trial_check", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        ]
        
        # Add missing columns
        added_columns = []
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE user ADD COLUMN {column_name} {column_def}"
                    cursor.execute(sql)
                    added_columns.append(column_name)
                    print(f"✅ Added column: {column_name}")
                except sqlite3.Error as e:
                    print(f"⚠️  Warning adding {column_name}: {e}")
        
        # Update existing users with default trial values
        if added_columns:
            print("🔄 Updating existing users with default values...")
            
            # Calculate trial end date (7 days from trial start)
            cursor.execute("""
                UPDATE user 
                SET trial_end_date = datetime(trial_start_date, '+7 days')
                WHERE trial_end_date IS NULL
            """)
            
            # Set trial_active based on current date vs trial_end_date
            cursor.execute("""
                UPDATE user 
                SET trial_active = CASE 
                    WHEN datetime('now') <= trial_end_date THEN 1 
                    ELSE 0 
                END
                WHERE trial_active IS NULL
            """)
            
            # Update trial_status based on trial_active
            cursor.execute("""
                UPDATE user 
                SET trial_status = CASE 
                    WHEN trial_active = 1 THEN 'active' 
                    ELSE 'expired' 
                END
                WHERE trial_status = 'active' OR trial_status IS NULL
            """)
            
            print("✅ Updated existing users with trial information")
        
        conn.commit()
        conn.close()
        
        if added_columns:
            print(f"🎉 Migration completed! Added {len(added_columns)} columns:")
            for col in added_columns:
                print(f"   - {col}")
        else:
            print("✅ Database already up to date!")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

def verify_migration():
    """Verify that migration was successful"""
    db_path = 'src/database/app.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table schema
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        required_columns = [
            'trial_active', 'subscription_plan', 'subscription_status', 
            'plan', 'payment_required', 'stripe_customer_id'
        ]
        
        missing = [col for col in required_columns if col not in columns]
        
        if missing:
            print(f"❌ Migration incomplete. Missing columns: {missing}")
            return False
        else:
            print("✅ Migration verification successful!")
            
            # Show sample user data
            cursor.execute("SELECT id, username, trial_active, subscription_plan, trial_status FROM user LIMIT 3")
            users = cursor.fetchall()
            
            if users:
                print("\n📊 Sample user data:")
                for user in users:
                    print(f"   User {user[0]} ({user[1]}): trial_active={user[2]}, plan={user[3]}, status={user[4]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 GISO Invest Database Migration")
    print("=" * 40)
    
    success = migrate_database()
    
    if success:
        print("\n🔍 Verifying migration...")
        verify_migration()
        print("\n🎯 Migration complete! You can now restart your application.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")

