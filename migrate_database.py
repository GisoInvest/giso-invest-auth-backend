import os
import sys
import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """Migrate the database schema to include new columns and tables"""
    try:
        # Get database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'database', 'app.db')
        
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            return False
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            logger.error("User table not found in database")
            conn.close()
            return False
        
        # Get existing columns in user table
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns to user table
        columns_to_add = {
            'trial_active': 'BOOLEAN DEFAULT 1',
            'trial_start_date': 'TIMESTAMP',
            'trial_end_date': 'TIMESTAMP',
            'trial_days_used': 'INTEGER DEFAULT 0',
            'trial_status': 'VARCHAR(50) DEFAULT "active"',
            'subscription_plan': 'VARCHAR(50)',
            'subscription_status': 'VARCHAR(50)',
            'plan': 'VARCHAR(50)',
            'subscription_start_date': 'TIMESTAMP',
            'last_payment_date': 'TIMESTAMP',
            'next_billing_date': 'TIMESTAMP',
            'payment_required': 'BOOLEAN DEFAULT 0',
            'stripe_customer_id': 'VARCHAR(255)',
            'stripe_payment_intent_id': 'VARCHAR(255)',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'last_login': 'TIMESTAMP',
            'last_trial_check': 'TIMESTAMP'
        }
        
        for column, data_type in columns_to_add.items():
            if column not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column} {data_type}")
                    logger.info(f"Added column '{column}' to user table")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not add column '{column}': {str(e)}")
        
        # Create portfolio table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id VARCHAR(100) PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_value FLOAT DEFAULT 0.0,
            total_properties INTEGER DEFAULT 0,
            avg_roi FLOAT DEFAULT 0.0,
            share_id VARCHAR(100) UNIQUE,
            is_public BOOLEAN DEFAULT 0,
            deal_packages_json TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        """)
        logger.info("Created or verified portfolio table")
        
        # Create property table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS property (
            id VARCHAR(100) PRIMARY KEY,
            user_id INTEGER NOT NULL,
            address VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            price FLOAT,
            monthly_rent FLOAT,
            bedrooms INTEGER,
            bathrooms INTEGER,
            property_type VARCHAR(50),
            strategy VARCHAR(50),
            roi FLOAT,
            details_json TEXT,
            analysis_json TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        """)
        logger.info("Created or verified property table")
        
        # Create report table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS report (
            id VARCHAR(100) PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            report_type VARCHAR(50) NOT NULL DEFAULT 'investment_analysis',
            content_json TEXT,
            properties_json TEXT,
            property_count INTEGER DEFAULT 0,
            avg_roi FLOAT DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        """)
        logger.info("Created or verified report table")
        
        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_user_id ON portfolio (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_user_id ON property (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_user_id ON report (user_id)")
        logger.info("Created or verified indexes")
        
        # Set default values for existing users
        cursor.execute("""
        UPDATE user 
        SET 
            trial_active = 1,
            trial_status = 'active',
            subscription_status = 'trial',
            created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE trial_active IS NULL
        """)
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    if migrate_database():
        print("Database migration completed successfully")
    else:
        print("Database migration failed")
        sys.exit(1)

