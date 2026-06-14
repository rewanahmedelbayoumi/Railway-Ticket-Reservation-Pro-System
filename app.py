from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database initialization
def init_db():
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Trains (
            train_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_time DATETIME NOT NULL,
            seats_available INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Bookings (
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
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        try:
            conn = sqlite3.connect('tickets.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Users (name, email, password) VALUES (?, ?, ?)', 
                          (name, email, password))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists!')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('tickets.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', name=session['name'])

@app.route('/trains')
def trains():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    source = request.args.get('source')
    destination = request.args.get('destination')
    date = request.args.get('date')
    
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    query = 'SELECT * FROM Trains WHERE 1=1'
    params = []
    
    if source:
        query += ' AND source = ?'
        params.append(source)
    if destination:
        query += ' AND destination = ?'
        params.append(destination)
    if date:
        query += ' AND date(departure_time) = ?'
        params.append(date)
    
    cursor.execute(query, params)
    trains = cursor.fetchall()
    conn.close()
    
    return render_template('trains.html', trains=trains)

@app.route('/book/<int:train_id>', methods=['GET', 'POST'])
def book(train_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Check seat availability
        cursor.execute('SELECT seats_available FROM Trains WHERE train_id = ?', (train_id,))
        seats = cursor.fetchone()[0]
        
        if seats > 0:
            # Book ticket
            cursor.execute('INSERT INTO Bookings (user_id, train_id, seat_number) VALUES (?, ?, ?)',
                          (session['user_id'], train_id, seats))
            # Update seat count
            cursor.execute('UPDATE Trains SET seats_available = seats_available - 1 WHERE train_id = ?',
                          (train_id,))
            conn.commit()
            flash('Booking successful!')
        else:
            flash('No seats available!')
        
        conn.close()
        return redirect(url_for('my_bookings'))
    
    # GET method - show train details
    cursor.execute('SELECT * FROM Trains WHERE train_id = ?', (train_id,))
    train = cursor.fetchone()
    conn.close()
    
    return render_template('book.html', train=train)

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.booking_id, t.source, t.destination, t.departure_time, b.booking_time, b.status 
        FROM Bookings b
        JOIN Trains t ON b.train_id = t.train_id
        WHERE b.user_id = ?
    ''', (session['user_id'],))
    bookings = cursor.fetchall()
    conn.close()
    
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/cancel/<int:booking_id>')
def cancel(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    # Get train_id for this booking
    cursor.execute('SELECT train_id FROM Bookings WHERE booking_id = ?', (booking_id,))
    train_id = cursor.fetchone()[0]
    
    # Update booking status
    cursor.execute('UPDATE Bookings SET status = "cancelled" WHERE booking_id = ?', (booking_id,))
    
    # Increase seat count
    cursor.execute('UPDATE Trains SET seats_available = seats_available + 1 WHERE train_id = ?', (train_id,))
    
    conn.commit()
    conn.close()
    
    flash('Booking cancelled successfully!')
    return redirect(url_for('my_bookings'))

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    return render_template('admin.html')

@app.route('/admin/trains')
def admin_trains():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Trains')
    trains = cursor.fetchall()
    conn.close()
    
    return render_template('admin_trains.html', trains=trains)

@app.route('/admin/add_train', methods=['GET', 'POST'])
def add_train():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        departure_time = request.form['departure_time']
        seats = int(request.form['seats'])
        
        conn = sqlite3.connect('tickets.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Trains (source, destination, departure_time, seats_available) VALUES (?, ?, ?, ?)',
                      (source, destination, departure_time, seats))
        conn.commit()
        conn.close()
        
        flash('Train added successfully!')
        return redirect(url_for('admin_trains'))
    
    return render_template('add_train.html')

@app.route('/admin/delete_train/<int:train_id>', methods=['POST'])
def delete_train(train_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    try:
        # Check if there are any bookings for this train
        cursor.execute('SELECT COUNT(*) FROM Bookings WHERE train_id = ? AND status = "active"', (train_id,))
        active_bookings = cursor.fetchone()[0]
        
        if active_bookings > 0:
            flash('Cannot delete train with active bookings!', 'error')
        else:
            cursor.execute('DELETE FROM Trains WHERE train_id = ?', (train_id,))
            conn.commit()
            flash('Train deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting train: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_trains'))

@app.route('/admin/edit_train/<int:train_id>', methods=['GET', 'POST'])
def edit_train(train_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        departure_time = request.form['departure_time']
        seats = int(request.form['seats'])
        
        try:
            cursor.execute('''
                UPDATE Trains 
                SET source = ?, destination = ?, departure_time = ?, seats_available = ?
                WHERE train_id = ?
            ''', (source, destination, departure_time, seats, train_id))
            conn.commit()
            flash('Train updated successfully!', 'success')
            return redirect(url_for('admin_trains'))
        except Exception as e:
            conn.rollback()
            flash(f'Error updating train: {str(e)}', 'error')
        finally:
            conn.close()
    else:
        cursor.execute('SELECT * FROM Trains WHERE train_id = ?', (train_id,))
        train = cursor.fetchone()
        conn.close()
        return render_template('edit_train.html', train=train)

@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    try:
        # Get booking statistics
        cursor.execute('''
            SELECT COUNT(*) as total_bookings,
                   SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_bookings,
                   SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_bookings
            FROM Bookings
        ''')
        booking_stats = cursor.fetchone()
        
        # Get popular routes
        cursor.execute('''
            SELECT t.source, t.destination, COUNT(b.booking_id) as bookings_count
            FROM Bookings b
            JOIN Trains t ON b.train_id = t.train_id
            GROUP BY t.source, t.destination
            ORDER BY bookings_count DESC
            LIMIT 5
        ''')
        popular_routes = cursor.fetchall()
        
        # Try to get revenue data (works even if Payments table doesn't exist)
        revenue_data = []
        try:
            cursor.execute('''
                SELECT strftime('%Y-%m', booking_time) as month,
                       COUNT(*) as bookings,
                       COALESCE(SUM(amount), 0) as revenue
                FROM Bookings
                LEFT JOIN Payments ON Bookings.booking_id = Payments.booking_id
                WHERE Bookings.booking_time > date('now', '-6 months')
                GROUP BY month
                ORDER BY month
            ''')
            revenue_data = cursor.fetchall()
        except sqlite3.OperationalError:
            # If Payments table doesn't exist, use base prices
            cursor.execute('''
                SELECT strftime('%Y-%m', b.booking_time) as month,
                       COUNT(*) as bookings,
                       COALESCE(SUM(t.base_price), 0) as revenue
                FROM Bookings b
                JOIN Trains t ON b.train_id = t.train_id
                WHERE b.booking_time > date('now', '-6 months')
                GROUP BY month
                ORDER BY month
            ''')
            revenue_data = cursor.fetchall()
        
        return render_template('admin_reports.html',
                             booking_stats=booking_stats,
                             popular_routes=popular_routes,
                             revenue_data=revenue_data)
        
    except Exception as e:
        flash(f'Error generating reports: {str(e)}', 'error')
        return redirect(url_for('admin'))
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)