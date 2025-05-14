from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import logging
import requests
import time
import jwt
from datetime import datetime
from db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# Konfigurasi ThingsBoard
THINGSBOARD_URL = "http://181.17.0.133:8080"
DEVICE_TOKEN = "bb05f420-1ffa-11f0-a0bc-33b4e39bb6f7"
USERNAME = "tenant@qtech.com"
PASSWORD = "tenant1140"

# Variabel global untuk menyimpan token
JWT_TOKEN = None
REFRESH_TOKEN = None

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Inisialisasi database
with app.app_context():
    init_db()
    conn = get_db_connection()
    try:
        conn.execute('ALTER TABLE bookings ADD COLUMN booking_time TEXT')
        conn.execute('ALTER TABLE bookings ADD COLUMN duration INTEGER')
        conn.execute('ALTER TABLE bookings ADD COLUMN remaining_duration INTEGER')
    except sqlite3.OperationalError:
        pass
    conn.execute('''
        CREATE TABLE IF NOT EXISTS booking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            slot_id TEXT,
            booking_time TEXT,
            duration INTEGER,
            total_price INTEGER,
            end_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS marked_vehicles (
            user_id INTEGER,
            slot_id TEXT,
            PRIMARY KEY (user_id, slot_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Dictionary untuk terjemahan bahasa
translations = {
    'en': {
        'title': 'Find Space - Book Your Slot',
        'nav_home': 'Home',
        'nav_features': 'Features',
        'nav_login': 'Login',
        'nav_register': 'Register',
        'hero_title': 'Find Space, Made Simple',
        'hero_subtitle': 'Discover and book your parking space with cutting-edge IoT technology.',
        'cta_button': 'Find a Space Now',
        'features_title': 'Why Choose Find Space?',
        'feature1_title': 'Real-Time Availability',
        'feature1_desc': 'Check parking space status instantly with our IoT-powered sensors.',
        'feature2_title': 'Easy Booking',
        'feature2_desc': 'Reserve your space in seconds from your phone or laptop.',
        'feature3_title': 'Secure & Reliable',
        'feature3_desc': 'Your parking space is safe with our advanced monitoring system.',
        'footer': '© 2025 Find Space. All rights reserved.',
    },
    'id': {
        'title': 'Cari Ruang - Pesan Slot Anda',
        'nav_home': 'Beranda',
        'nav_features': 'Fitur',
        'nav_login': 'Masuk',
        'nav_register': 'Daftar',
        'hero_title': 'Cari Ruang, Dibuat Sederhana',
        'hero_subtitle': 'Temukan dan pesan ruang parkir Anda dengan teknologi IoT mutakhir.',
        'cta_button': 'Cari Ruang Sekarang',
        'features_title': 'Mengapa Memilih Cari Ruang?',
        'feature1_title': 'Ketersediaan Real-Time',
        'feature1_desc': 'Periksa status ruang parkir secara instan dengan sensor bertenaga IoT kami.',
        'feature2_title': 'Pemesanan Mudah',
        'feature2_desc': 'Pesan ruang Anda dalam hitungan detik dari ponsel atau laptop Anda.',
        'feature3_title': 'Aman & Terpercaya',
        'feature3_desc': 'Ruang parkir Anda aman dengan sistem pemantauan canggih kami.',
        'footer': '© 2025 Cari Ruang. Semua hak dilindungi.',
    }
}

# Route untuk mengatur bahasa
@app.route('/set_language/<lang>')
def set_language(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('index'))

# Jinja Filter: format angka
@app.template_filter('format_number')
def format_number(value):
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return str(value)

# Fungsi untuk memeriksa masa berlaku token
def is_token_expired(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get("exp")
        current_time = int(time.time())
        return exp < current_time
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return True

# Fungsi untuk memperbarui token
def refresh_jwt_token():
    global JWT_TOKEN, REFRESH_TOKEN
    try:
        resp = requests.post(
            f"{THINGSBOARD_URL}/api/auth/token",
            headers={"Content-Type": "application/json"},
            json={"refreshToken": REFRESH_TOKEN},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        JWT_TOKEN = data["token"]
        REFRESH_TOKEN = data["refreshToken"]
        logger.info("JWT Token refreshed successfully")
        return True
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return False

# Fungsi untuk login ke ThingsBoard
def login_to_thingsboard():
    global JWT_TOKEN, REFRESH_TOKEN
    try:
        resp = requests.post(
            f"{THINGSBOARD_URL}/api/auth/login",
            headers={"Content-Type": "application/json"},
            json={"username": USERNAME, "password": PASSWORD},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        JWT_TOKEN = data["token"]
        REFRESH_TOKEN = data["refreshToken"]
        logger.info("Logged in successfully")
        return True
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        return False

# Fungsi untuk mendapatkan token yang valid
def get_valid_token():
    global JWT_TOKEN
    if JWT_TOKEN is None or is_token_expired(JWT_TOKEN):
        logger.info("JWT Token expired or not set, attempting to refresh")
        if REFRESH_TOKEN and refresh_jwt_token():
            return JWT_TOKEN
        logger.info("Refresh token failed, attempting to login")
        if login_to_thingsboard():
            return JWT_TOKEN
        raise Exception("Failed to obtain a valid token")
    return JWT_TOKEN

# Halaman beranda
@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    lang = session.get('language', 'en')
    return render_template('index.html', translations=translations[lang], lang=lang)

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    lang = session.get('language', 'en')
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'info')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already taken!', 'danger')
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            flash('An error occurred during registration.', 'danger')
        finally:
            conn.close()
    return render_template('register.html', translations=translations[lang])

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    lang = session.get('language', 'en')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?',
                (username,)
            ).fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect username or password!', 'danger')
        except Exception as e:
            logger.error(f"Error during login: {e}")
            flash('An error occurred during login.', 'danger')
        finally:
            conn.close()
    return render_template('login.html', translations=translations[lang], username="")

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    lang = session.get('language', 'en')
    user_id = session.get('user_id')
    return render_template('dashboard.html', user_id=user_id, translations=translations[lang], lang=lang)

# BOOK SLOT
@app.route('/book/<slot_id>', methods=['POST'])
def book_slot(slot_id):
    if 'user_id' not in session:
        flash('Please login to book a slot.', 'danger')
        return redirect(url_for('login'))

    hours = request.form.get('hours')
    minutes = request.form.get('minutes')
    if not hours or not minutes:
        flash('Duration is required.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        hours = int(hours)
        minutes = int(minutes)
        if hours < 0 or minutes < 0 or (hours == 0 and minutes == 0):
            flash('Minimum duration is 1 minute.', 'danger')
            return redirect(url_for('dashboard'))
        if hours > 24 or (hours == 24 and minutes > 0):
            flash('Maximum duration is 24 hours.', 'danger')
            return redirect(url_for('dashboard'))
        if minutes >= 60:
            flash('Minutes must be less than 60.', 'danger')
            return redirect(url_for('dashboard'))

        duration = (hours * 60) + minutes
        total_price = (hours * 5000) + (minutes * 830)
        booking_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        remaining_duration = duration

        # Update ThingsBoard
        token = get_valid_token()
        slot_number = '1' if slot_id == 'A1' else '2' if slot_id == 'A2' else '3' if slot_id == 'A3' else '4' if slot_id == 'A4' else '0'
        booked_key = f"slot{slot_number}_booked"
        lamp_key = f"lamp{slot_number}"
        payload = {booked_key: True, lamp_key: False}
        resp = requests.post(
            f"{THINGSBOARD_URL}/api/plugins/telemetry/DEVICE/{DEVICE_TOKEN}/SHARED_SCOPE",
            headers={"X-Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=5
        )
        resp.raise_for_status()

        # Simpan ke database
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO bookings (user_id, slot_id, booking_time, duration, remaining_duration, total_price) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (session['user_id'], slot_id, booking_time, duration, remaining_duration, total_price)
        )
        conn.commit()
        conn.close()
        flash(f'Slot {slot_id} booked successfully (Rp{total_price:,}).', 'success')

    except Exception as e:
        logger.error(f"Error booking slot: {e}")
        flash('Failed to book the slot.', 'danger')
        return redirect(url_for('dashboard'))

    return redirect(url_for('dashboard'))

# UNBOOK SLOT
@app.route('/unbook/<slot_id>', methods=['POST'])
def unbook_slot(slot_id):
    if 'user_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    try:
        # Update ThingsBoard
        token = get_valid_token()
        slot_number = '1' if slot_id == 'A1' else '2' if slot_id == 'A2' else '3' if slot_id == 'A3' else '4' if slot_id == 'A4' else '0'
        booked_key = f"slot{slot_number}_booked"
        lamp_key = f"lamp{slot_number}"
        payload = {booked_key: False, lamp_key: True}
        resp = requests.post(
            f"{THINGSBOARD_URL}/api/plugins/telemetry/DEVICE/{DEVICE_TOKEN}/SHARED_SCOPE",
            headers={"X-Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=5
        )
        resp.raise_for_status()

        # Update database
        conn = get_db_connection()
        booking = conn.execute(
            'SELECT user_id, slot_id, booking_time, duration, total_price FROM bookings WHERE slot_id = ?',
            (slot_id,)
        ).fetchone()
        if booking:
            if session.get('role') == 'admin' or booking['user_id'] == session['user_id']:
                end_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                conn.execute(
                    'INSERT INTO booking_history (user_id, slot_id, booking_time, duration, total_price, end_time) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (booking['user_id'], booking['slot_id'], booking['booking_time'], booking['duration'], booking['total_price'], end_time)
                )
                conn.execute('DELETE FROM bookings WHERE slot_id = ?', (slot_id,))
                conn.commit()
                flash(f'Slot {slot_id} has been released.', 'info')
            else:
                flash('You do not have permission to release this booking.', 'danger')
        else:
            flash('Booking not found.', 'danger')

    except Exception as e:
        logger.error(f"Error unbooking slot: {e}")
        flash('Failed to release the booking.', 'danger')

    return redirect(url_for('dashboard'))

# MARK VEHICLE
@app.route('/mark_vehicle/<slot_id>', methods=['POST'])
def mark_vehicle(slot_id):
    if 'user_id' not in session:
        flash('Please login to mark a vehicle.', 'danger')
        return redirect(url_for('login'))

    action = request.form.get('action')
    conn = get_db_connection()
    try:
        if action == 'mark':
            conn.execute(
                'INSERT OR REPLACE INTO marked_vehicles (user_id, slot_id) VALUES (?, ?)',
                (session['user_id'], slot_id)
            )
            flash(f'Slot {slot_id} marked as your vehicle.', 'success')
        elif action == 'unmark':
            conn.execute(
                'DELETE FROM marked_vehicles WHERE user_id = ? AND slot_id = ?',
                (session['user_id'], slot_id)
            )
            flash(f'Slot {slot_id} unmarked.', 'info')
        conn.commit()
    except Exception as e:
        logger.error(f"Error marking vehicle: {e}")
        flash('Failed to mark the vehicle.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

# API STATUS
@app.route('/api/status')
def get_status():
    try:
        token = get_valid_token()
        resp = requests.get(
            f"{THINGSBOARD_URL}/api/plugins/telemetry/DEVICE/{DEVICE_TOKEN}/values/timeseries",
            headers={"X-Authorization": f"Bearer {token}"},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        attr_resp = requests.get(
            f"{THINGSBOARD_URL}/api/plugins/telemetry/DEVICE/{DEVICE_TOKEN}/values/attributes",
            headers={"X-Authorization": f"Bearer {token}"},
            timeout=5
        )
        attr_resp.raise_for_status()
        attr_data = attr_resp.json()
        booked = {
            "slot1_booked": False,
            "slot2_booked": False,
            "slot3_booked": False,
            "slot4_booked": False
        }
        for attr in attr_data:
            if attr["key"] == "slot1_booked":
                booked["slot1_booked"] = attr["value"]
            elif attr["key"] == "slot2_booked":
                booked["slot2_booked"] = attr["value"]
            elif attr["key"] == "slot3_booked":
                booked["slot3_booked"] = attr["value"]
            elif attr["key"] == "slot4_booked":
                booked["slot4_booked"] = attr["value"]

        conn = get_db_connection()
        bookings = conn.execute('SELECT slot_id FROM bookings').fetchall()
        slot_ids = [booking['slot_id'] for booking in bookings]
        for slot_id in ['A1', 'A2', 'A3', 'A4']:
            slot_number = '1' if slot_id == 'A1' else '2' if slot_id == 'A2' else '3' if slot_id == 'A3' else '4' if slot_id == 'A4' else '0'
            booked_key = f"slot{slot_number}_booked"
            is_booked = slot_id in slot_ids
            if booked[booked_key] != is_booked:
                payload = {booked_key: is_booked}
                requests.post(
                    f"{THINGSBOARD_URL}/api/plugins/telemetry/DEVICE/{DEVICE_TOKEN}/SHARED_SCOPE",
                    headers={"X-Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=5
                )

        # Cek status occupied untuk setiap slot dan hapus marked_vehicles jika slot kosong
        slot_map = {
            'A1': data.get('slot1_occupied', [{'value': False}])[0]['value'],
            'A2': data.get('slot2_occupied', [{'value': False}])[0]['value'],
            'A3': data.get('slot3_occupied', [{'value': False}])[0]['value'],
            'A4': data.get('slot4_occupied', [{'value': False}])[0]['value']
        }
        for slot_id, occupied in slot_map.items():
            is_occupied = occupied == True or occupied == "true" or occupied == 1 or occupied == "1"
            if not is_occupied:  # Jika slot kosong, hapus semua entri marked_vehicles untuk slot ini
                conn.execute('DELETE FROM marked_vehicles WHERE slot_id = ?', (slot_id,))
                logger.info(f"Cleared marked_vehicles for slot {slot_id} as it is now empty")

        marked_vehicles = conn.execute(
            'SELECT slot_id FROM marked_vehicles WHERE user_id = ?',
            (session.get('user_id'),)
        ).fetchall()
        marked_slots = [mv['slot_id'] for mv in marked_vehicles]

        now = datetime.now()
        rows = conn.execute(
            'SELECT id, slot_id, user_id, booking_time, duration, remaining_duration, total_price FROM bookings'
        ).fetchall()
        expired_bookings = []
        for r in rows:
            booking_time = datetime.strptime(r['booking_time'], '%Y-%m-%d %H:%M')
            duration_seconds = r['duration'] * 60
            elapsed_seconds = (now - booking_time).total_seconds()
            remaining_seconds = duration_seconds - elapsed_seconds
            remaining_minutes = max(0, int(remaining_seconds / 60))
            conn.execute('UPDATE bookings SET remaining_duration = ? WHERE id = ?', (remaining_minutes, r['id']))
            if remaining_seconds <= 0:
                end_time = now.strftime('%Y-%m-%d %H:%M')
                conn.execute(
                    'INSERT INTO booking_history (user_id, slot_id, booking_time, duration, total_price, end_time) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (r['user_id'], r['slot_id'], r['booking_time'], r['duration'], r['total_price'], end_time)
                )
                conn.execute('DELETE FROM bookings WHERE id = ?', (r['id'],))
                expired_bookings.append({'slot_id': r['slot_id'], 'user_id': r['user_id']})
                slot_number = '1' if r['slot_id'] == 'A1' else '2' if r['slot_id'] == 'A2' else '3' if r['slot_id'] == 'A3' else '4' if r['slot_id'] == 'A4' else '0'
                booked_key = f"slot{slot_number}_booked"
                lamp_key = f"lamp{slot_number}"
                payload = {booked_key: False, lamp_key: True}
                requests.post(
                    f"{THINGSBOARD_URL}/api/plugins/telemetry/DEVICE/{DEVICE_TOKEN}/SHARED_SCOPE",
                    headers={"X-Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=5
                )
        conn.commit()

        rows2 = conn.execute('''
            SELECT b.slot_id, b.user_id, b.booking_time, b.duration, b.remaining_duration, b.total_price, u.username
            FROM bookings b JOIN users u ON b.user_id = u.id
        ''').fetchall()
        conn.close()

        bookings_list = []
        for b in rows2:
            bookings_list.append({
                'slot_id': b['slot_id'],
                'user_id': b['user_id'],
                'username': b['username'] if session.get('role') == 'admin' else None,
                'booking_time': b['booking_time'],
                'duration': b['duration'],
                'remaining_duration': b['remaining_duration'],
                'total_price': b['total_price'],
            })

        return jsonify({
            'slot1': {
                'occupied': data.get('slot1_occupied', [{'value': False}])[0]['value'],
                'booked': booked['slot1_booked']
            },
            'slot2': {
                'occupied': data.get('slot2_occupied', [{'value': False}])[0]['value'],
                'booked': booked['slot2_booked']
            },
            'slot3': {
                'occupied': data.get('slot3_occupied', [{'value': False}])[0]['value'],
                'booked': booked['slot3_booked']
            },
            'slot4': {
                'occupied': data.get('slot4_occupied', [{'value': False}])[0]['value'],
                'booked': booked['slot4_booked']
            },
            'bookings': bookings_list,
            'expired_bookings': expired_bookings,
            'current_user': session.get('user_id'),
            'session_username': session.get('username'),
            'session_role': session.get('role'),
            'marked_slots': marked_slots
        })

    except Exception as e:
        logger.error(f"Error in get_status: {e}")
        return jsonify({'error': str(e)}), 500

# USER HISTORY
@app.route('/history')
def user_history():
    lang = session.get('language', 'en')
    if 'user_id' not in session:
        flash('Please login to view your history.', 'danger')
        return redirect(url_for('login'))
    conn = get_db_connection()
    try:
        data = conn.execute('''
            SELECT slot_id, booking_time, duration, total_price, end_time
            FROM booking_history WHERE user_id = ? ORDER BY booking_time DESC
        ''', (session['user_id'],)).fetchall()
        history = [{'slot_id': b['slot_id'], 'booking_time': b['booking_time'], 'duration': b['duration'], 'total_price': b['total_price'], 'end_time': b['end_time']} for b in data]
    except Exception as e:
        logger.error(f"Error user_history: {e}")
        flash('Failed to load history.', 'danger')
        history = []
    finally:
        conn.close()
    return render_template('user_history.html', history=history, translations=translations[lang])

# ADMIN HISTORY
@app.route('/admin/history')
def admin_history():
    lang = session.get('language', 'en')
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    try:
        data = conn.execute('''
            SELECT b.slot_id, b.booking_time, b.duration, b.total_price, b.end_time, u.username
            FROM booking_history b JOIN users u ON b.user_id = u.id
            ORDER BY b.booking_time DESC
        ''').fetchall()
        history = [{'slot_id': b['slot_id'], 'username': b['username'], 'booking_time': b['booking_time'], 'duration': b['duration'], 'total_price': b['total_price'], 'end_time': b['end_time']} for b in data]
    except Exception as e:
        logger.error(f"Error admin_history: {e}")
        flash('Failed to load history.', 'danger')
        history = []
    finally:
        conn.close()
    return render_template('admin_history.html', history=history, translations=translations[lang])

# ADMIN PANEL
@app.route('/admin')
def admin_panel():
    lang = session.get('language', 'en')
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    try:
        data = conn.execute('''
            SELECT b.id, b.slot_id, b.booking_time, b.duration, b.remaining_duration, b.total_price, u.username
            FROM bookings b JOIN users u ON b.user_id = u.id
        ''').fetchall()
        bookings = [{'id': b['id'], 'slot_id': b['slot_id'], 'booking_time': b['booking_time'], 'duration': b['duration'], 'remaining_duration': b['remaining_duration'], 'total_price': b['total_price'], 'username': b['username']} for b in data]
    except Exception as e:
        logger.error(f"Error admin_panel: {e}")
        flash('Failed to load data.', 'danger')
        bookings = []
    finally:
        conn.close()
    return render_template('admin_panel.html', bookings=bookings, translations=translations[lang])

# ADMIN USERS
@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    lang = session.get('language', 'en')
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            hashed_password = generate_password_hash(password)
            conn.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, hashed_password, 'user')
            )
            conn.commit()
            flash(f'User {username} added successfully.', 'success')
        users = conn.execute('SELECT id, username, role FROM users').fetchall()
    except sqlite3.IntegrityError:
        flash('Username already taken!', 'danger')
        users = conn.execute('SELECT id, username, role FROM users').fetchall()
    except Exception as e:
        logger.error(f"Error admin_users: {e}")
        flash('An error occurred.', 'danger')
        users = []
    finally:
        conn.close()
    return render_template('admin_users.html', users=users, translations=translations[lang])

# DELETE USER
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if user['username'] == 'admin':
            flash('Cannot delete the admin user!', 'danger')
        else:
            conn.execute('DELETE FROM bookings WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM booking_history WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            flash('User deleted successfully.', 'info')
    except Exception as e:
        logger.error(f"Error delete_user: {e}")
        flash('Failed to delete the user.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin_users'))

# CONFIRM SLOT
@app.route('/api/confirm_slot/<int:slot>/<string:confirm>', methods=['POST'])
def confirm_slot(slot, confirm):
    try:
        token = get_valid_token()
        booked_key = f"slot{slot}_booked"
        lamp_key = f"lamp{slot}"
        payload = {}
        if confirm.lower() == "yes":
            payload = {
                booked_key: False,
                lamp_key: True
            }
            slot_id = 'A1' if slot == 1 else 'A2' if slot == 2 else 'A3' if slot == 3 else 'A4'
            conn = get_db_connection()
            booking = conn.execute(
                'SELECT user_id, slot_id, booking_time, duration, total_price FROM bookings WHERE slot_id = ?',
                (slot_id,)
            ).fetchone()
            if booking:
                end_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                conn.execute(
                    'INSERT INTO booking_history (user_id, slot_id, booking_time, duration, total_price, end_time) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (booking['user_id'], booking['slot_id'], booking['booking_time'], booking['duration'], booking['total_price'], end_time)
                )
                conn.execute('DELETE FROM bookings WHERE slot_id = ?', (slot_id,))
                conn.commit()
            conn.close()
        else:
            payload = {
                booked_key: True,
                lamp_key: False
            }
        resp = requests.post(
            f"{THINGSBOARD_URL}/api/plugins/telemetry/DEVICE/{DEVICE_TOKEN}/SHARED_SCOPE",
            headers={"X-Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=5
        )
        resp.raise_for_status()
        return jsonify({"status": "success", "message": f"Slot {slot} confirmation: {confirm}"})
    except Exception as e:
        logger.error(f"Error confirming slot: {e}")
        return jsonify({"error": "Failed to confirm slot"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=81)
