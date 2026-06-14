# migrate_db.py
import sqlite3

def migrate_database():
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    try:
        # Create Payments table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER UNIQUE NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id)
            )
        ''')
        
        # Add base_price column to Trains if it doesn't exist
        try:
            cursor.execute('ALTER TABLE Trains ADD COLUMN base_price DECIMAL(10,2) DEFAULT 100.00')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        conn.commit()
        print("✅ Database migrated successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()