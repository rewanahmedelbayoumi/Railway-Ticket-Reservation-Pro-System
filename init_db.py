import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def initialize_database():
    # Connect to SQLite database (creates it if doesn't exist)
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    try:
        # Drop tables if they exist (for clean initialization)
        cursor.execute("DROP TABLE IF EXISTS Payments")
        cursor.execute("DROP TABLE IF EXISTS Bookings")
        cursor.execute("DROP TABLE IF EXISTS Trains")
        cursor.execute("DROP TABLE IF EXISTS Users")
        
        # Create Users table
        cursor.execute('''
            CREATE TABLE Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        ''')
        
        # Create Trains table
        cursor.execute('''
            CREATE TABLE Trains (
                train_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                departure_time DATETIME NOT NULL,
                seats_available INTEGER NOT NULL,
                base_price DECIMAL(10,2) DEFAULT 100.00
            )
        ''')
        
        # Create Bookings table
        cursor.execute('''
            CREATE TABLE Bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                train_id INTEGER NOT NULL,
                booking_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                seat_number INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (train_id) REFERENCES Trains(train_id)
            )
        ''')
        
        # Create Payments table
        cursor.execute('''
            CREATE TABLE Payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER UNIQUE NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id)
            )
        ''')
        
        # Insert sample users (with hashed passwords)
        users = [
            ('Admin User', 'admin@railelegance.com', generate_password_hash('admin123'), 'admin'),
            ('Passenger One', 'passenger1@test.com', generate_password_hash('pass123'), 'user'),
            ('Passenger Two', 'passenger2@test.com', generate_password_hash('pass456'), 'user')
        ]
        cursor.executemany('INSERT INTO Users (name, email, password, role) VALUES (?, ?, ?, ?)', users)
        
        # Insert sample trains with realistic dates and prices
        trains = [
            ('Cairo', 'Alexandria', '2025-07-01 08:00:00', 50, 150.00),
            ('Luxor', 'Aswan', '2025-07-02 10:30:00', 30, 200.00),
            ('Giza', 'Hurghada', '2025-07-03 14:15:00', 45, 180.00),
            ('Cairo', 'Luxor', '2025-07-05 20:00:00', 60, 350.00),
            ('Alexandria', 'Aswan', '2025-07-10 07:30:00', 40, 400.00)
        ]
        cursor.executemany('INSERT INTO Trains (source, destination, departure_time, seats_available, base_price) VALUES (?, ?, ?, ?, ?)', trains)
        
        # Insert sample bookings with realistic dates
        bookings = [
            (2, 1, 15, 'active', '2025-06-01 10:15:00'),  # Passenger 1 booked train 1
            (3, 2, 5, 'active', '2025-06-02 11:30:00'),    # Passenger 2 booked train 2
            (2, 3, 22, 'cancelled', '2025-06-03 09:45:00'), # Cancelled booking
            (3, 1, 8, 'active', '2025-06-10 14:20:00')      # Another booking
        ]
        cursor.executemany('INSERT INTO Bookings (user_id, train_id, seat_number, status, booking_time) VALUES (?, ?, ?, ?, ?)', bookings)
        
        # Insert sample payments
        payments = [
            (1, 150.00, 'completed', '2025-06-01 10:20:00'),
            (2, 200.00, 'completed', '2025-06-02 11:35:00'),
            (4, 150.00, 'refunded', '2025-06-10 14:25:00')
        ]
        cursor.executemany('INSERT INTO Payments (booking_id, amount, status, payment_date) VALUES (?, ?, ?, ?)', payments)
        
        # Insert historical data for reports
        for i in range(1, 6):
            past_date = datetime.now() - timedelta(days=30*i)
            booking_date = past_date.strftime('%Y-%m-%d %H:%M:%S')
            payment_date = (past_date + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(
                'INSERT INTO Bookings (user_id, train_id, seat_number, booking_time) VALUES (?, ?, ?, ?)',
                (2 if i%2 else 3, 1 if i%3 else 2, 10+i, booking_date)
            )
            booking_id = cursor.lastrowid
            
            cursor.execute(
                'INSERT INTO Payments (booking_id, amount, payment_date) VALUES (?, ?, ?)',
                (booking_id, 150.00 + (i*20), payment_date)
            )
        
        conn.commit()
        print("✅ Database initialized successfully with sample data!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()