# -*- coding: utf-8 -*-

#!/usr/bin/env python3

import os
import sqlite3
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify, Response, send_from_directory, send_file
from flask_cors import CORS
import requests
from datetime import datetime
from PIL import Image
import io
import atexit
import shutil
import zipfile
from firebase_config import initialize_firebase
from device_manager import DeviceManager
from cache_manager import CacheManager
import mimetypes
from version import VERSION
import subprocess
import time
import cx_Oracle
from oracle_config import initialize_oracle
import logging

# Set Oracle client encoding
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"

# Constants
DISPLAY_DIR = os.path.dirname(os.path.abspath(__file__))  # This is the display directory
PROJECT_ROOT = os.path.dirname(DISPLAY_DIR)  # This is the project root
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")  # Static files are in project root
DISPLAY_STATIC_DIR = os.path.join(DISPLAY_DIR, "static")  # React build is in display/static
MEDIA_FOLDER = os.path.join(STATIC_DIR, "media")
CACHE_DIR = os.path.join(PROJECT_ROOT, "cache")
UPDATES_DIR = os.path.join(PROJECT_ROOT, "updates")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
DB_FILE = os.path.join(PROJECT_ROOT, "data", "kiosk.db")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}

# Create necessary directories
for directory in [MEDIA_FOLDER, UPLOAD_FOLDER, os.path.dirname(DB_FILE)]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Initialize SQLite database
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            media_path TEXT,
            duration INTEGER DEFAULT 10000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

init_db()

########################
# FLASK APP SETUP
########################
app = Flask(__name__, 
    static_folder=STATIC_DIR,  # Use root static folder
    static_url_path='/static'  # Keep the same URL path
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "admin")
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['PROPAGATE_EXCEPTIONS'] = True
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Enable CORS for development
CORS(app, supports_credentials=True, origins=['http://localhost:3000'])

# Force output to be flushed immediately

# Initialize Firebase managers
cache_manager = CacheManager()
db, storage, device_key = initialize_firebase()
if not device_key:
    raise ValueError("Device key not available. Please configure DEVICE_KEY in .env")

device_manager = DeviceManager(db, device_key, cache_manager.get_device_ip())

# Initialize device and group data
device, group = device_manager.initialize()
if group:
    cache_manager.set_cached_group(group)
    if group.get('media'):
        cache_manager.sync_media(group['media'])

@atexit.register
def cleanup():
    """Update device status to offline when shutting down"""
    if device_manager.device_doc:
        device_manager.update_device_status('offline')

# Ideal dimensions for 16:9 TV displays
RECOMMENDED_WIDTH = 1920
RECOMMENDED_HEIGHT = 1080
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(file_storage):
    """Process and validate uploaded image"""
    try:
        # Read the image
        img_bytes = file_storage.read()
        
        # Check file size
        if len(img_bytes) > MAX_FILE_SIZE:
            return None, "File size too large. Maximum size is 10MB."
            
        # Open the image
        img = Image.open(io.BytesIO(img_bytes))
        
        # Get dimensions
        width, height = img.size
        
        # Calculate aspect ratio
        aspect_ratio = width / height
        target_ratio = RECOMMENDED_WIDTH / RECOMMENDED_HEIGHT
        
        # Check if dimensions are too small
        if width < 800 or height < 600:
            return None, "Image dimensions too small. Minimum size is 800x600 pixels."
            
        # If it's a GIF, handle it specially to preserve animation
        if img.format == 'GIF' and 'duration' in img.info:
            # If GIF is too large, resize each frame
            if width > RECOMMENDED_WIDTH * 1.5 or height > RECOMMENDED_HEIGHT * 1.5:
                frames = []
                try:
                    while True:
                        if aspect_ratio > target_ratio:
                            new_width = RECOMMENDED_WIDTH
                            new_height = int(RECOMMENDED_WIDTH / aspect_ratio)
                        else:
                            new_height = RECOMMENDED_HEIGHT
                            new_width = int(RECOMMENDED_HEIGHT * aspect_ratio)
                            
                        frame = img.copy()
                        frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        frames.append(frame)
                        img.seek(img.tell() + 1)
                except EOFError:
                    pass  # End of frames
                
                # Save the resized GIF
                output = io.BytesIO()
                frames[0].save(
                    output,
                    format='GIF',
                    save_all=True,
                    append_images=frames[1:],
                    duration=img.info['duration'],
                    loop=img.info.get('loop', 0),
                    optimize=False
                )
            else:
                # If GIF is already good size, just optimize it
                output = io.BytesIO()
                img.save(
                    output,
                    format='GIF',
                    save_all=True,
                    optimize=False
                )
            return output.getvalue(), None
            
        # For non-GIF images that are too large, resize them
        if width > RECOMMENDED_WIDTH * 1.5 or height > RECOMMENDED_HEIGHT * 1.5:
            # Calculate new dimensions maintaining aspect ratio
            if aspect_ratio > target_ratio:
                new_width = RECOMMENDED_WIDTH
                new_height = int(RECOMMENDED_WIDTH / aspect_ratio)
            else:
                new_height = RECOMMENDED_HEIGHT
                new_width = int(RECOMMENDED_HEIGHT * aspect_ratio)
                
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        # Save to bytes for storage
        output = io.BytesIO()
        if img.format == 'PNG':
            img.save(output, format='PNG', optimize=True)
        else:
            img.save(output, format='JPEG', quality=85, optimize=True)
        
        return output.getvalue(), None
        
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

########################
# HELPER FUNCTIONS
########################
def get_weather_info():
    """Retrieves detailed weather info from OpenWeatherMap"""
    try:
        # Get config from Firestore
        weather_config = db.collection('config').document('openWeather').get()
        if weather_config.exists:
            config_data = weather_config.to_dict()
            api_key = config_data.get('apiKey')
            city = config_data.get('location')
        else:
            return None

        if not api_key or not city:
            return None

        # Get current weather
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=pt_br"
        r = requests.get(url)
        current_data = r.json()
        
        # Get forecast for min/max and rain chance
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=pt_br"
        forecast_r = requests.get(forecast_url)
        forecast_data = forecast_r.json()
        
        if current_data.get("cod") != 200:
            return None
            
        # Get today's forecast
        today_forecast = next((item for item in forecast_data['list'] 
                             if datetime.fromtimestamp(item['dt']).date() == datetime.now().date()), None)
        
        return {
            "city": city,
            "weather": current_data["weather"][0]["description"],
            "icon": current_data["weather"][0]["icon"],
            "temperature": round(current_data["main"]["temp"]),
            "temp_min": round(today_forecast["main"]["temp_min"] if today_forecast else current_data["main"]["temp_min"]),
            "temp_max": round(today_forecast["main"]["temp_max"] if today_forecast else current_data["main"]["temp_max"]),
            "rain_chance": round(today_forecast["pop"] * 100 if today_forecast else 0),
            "humidity": current_data["main"]["humidity"]
        }
    except Exception as e:
        print(f"Weather API error: {str(e)}")
        return None

def get_upcoming_birthdays():
    """Get upcoming birthdays from Oracle database"""
    try:
        print("\n=== Starting Birthday Query ===")
        # Oracle connection string
        dsn = cx_Oracle.makedsn('192.168.50.25', 1521, service_name='dic4')
        print(f"DSN Created: {dsn}")
        
        # Get today's date for comparison
        today = datetime.now().date()
        print(f"Today's date: {today}")
        
        # Connect to Oracle with proper encoding settings
        print("Attempting Oracle connection...")
        with cx_Oracle.connect(
            user='NCS', 
            password='ncsdgt2025', 
            dsn=dsn, 
            encoding="UTF-8", 
            nencoding="UTF-8"
        ) as connection:
            # Set a timeout at the session level instead
            cursor = connection.cursor()
            cursor.execute("ALTER SESSION SET NLS_LANGUAGE='BRAZILIAN PORTUGUESE'")
            cursor.execute("ALTER SESSION SET NLS_TERRITORY='BRAZIL'")
            cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT='YYYY-MM-DD'")
            # Set session timeout in seconds
            cursor.execute("BEGIN DBMS_SESSION.MODIFY_PACKAGE_STATE(2); END;")
            print("Session parameters set")
            
            # SQL query for upcoming birthdays
            sql = """
            SELECT 
                nome_colaborador,
                area,
                data_aniversario
            FROM (
                SELECT 
                    f.nm_funcionario AS nome_colaborador,
                    f.cd_area AS area,
                    f.dt_nascimento AS data_aniversario,
                    CASE
                        WHEN TO_DATE(
                            TO_CHAR(SYSDATE, 'YYYY') || 
                            TO_CHAR(f.dt_nascimento, 'MMDD'),
                            'YYYYMMDD'
                        ) >= TRUNC(SYSDATE)
                        THEN 
                            TO_DATE(
                                TO_CHAR(SYSDATE, 'YYYY') || 
                                TO_CHAR(f.dt_nascimento, 'MMDD'),
                                'YYYYMMDD'
                            )
                        ELSE 
                            ADD_MONTHS(
                                TO_DATE(
                                    TO_CHAR(SYSDATE, 'YYYY') || 
                                    TO_CHAR(f.dt_nascimento, 'MMDD'),
                                    'YYYYMMDD'
                                ),
                                12
                            )
                    END AS prox_aniversario
                FROM 
                    DIGITRO.FUNCIONARIO f
                WHERE 
                    f.DT_SAIDA IS NULL
                    AND f.dt_nascimento IS NOT NULL
                ORDER BY 
                    prox_aniversario
            )
            WHERE 
                ROWNUM <= 5
            """
            
            print("\nExecuting SQL query...")
            print("SQL Query:", sql)
            cursor.execute(sql)
            rows = cursor.fetchall()
            print(f"\nQuery returned {len(rows)} rows")
            
            # Debug print each row
            for i, row in enumerate(rows):
                print(f"\nRow {i + 1}:")
                print(f"  Name: {row[0] if row[0] else 'None'}")
                print(f"  Sector: {row[1] if row[1] else 'None'}")
                print(f"  Birth Date: {row[2] if row[2] else 'None'}")
            
            # Convert Oracle data to list of birthdays
            birthday_list = []
            for row in rows:
                name, sector, birth_date = row
                print(f"\nProcessing birthday for {name}:")
                
                # Format the date as YYYY-MM-DD string
                formatted_date = birth_date.strftime('%Y-%m-%d') if birth_date else None
                print(f"  Formatted date: {formatted_date}")
                
                if name and formatted_date:
                    # Check if birthday is today (compare month and day)
                    is_today = (birth_date.month == today.month and 
                              birth_date.day == today.day)
                    print(f"  Is today: {is_today}")
                    
                    birthday_entry = {
                        'name': name.strip(),
                        'sector': sector.strip() if sector else '',
                        'date': formatted_date,
                        'is_today': is_today
                    }
                    print(f"  Adding entry: {birthday_entry}")
                    birthday_list.append(birthday_entry)
                else:
                    print(f"  Skipping entry - Invalid name or date")
            
            print(f"\nFinal birthday list has {len(birthday_list)} entries")
            return birthday_list
            
    except Exception as e:
        print("\n=== Error in Birthday Query ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Traceback:")
        import traceback
        traceback.print_exc()
        return []

########################
# AUTHENTICATION
########################
def check_login():
    return session.get("logged_in", False)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Very basic password check. You can store hashed pass in DB
        if request.form.get("password") == "admin123":
            session["logged_in"] = True
            return redirect("/admin")
        else:
            return "Invalid password", 403
    return '''
    <form method="POST">
      <label>Password: <input type="password" name="password" /></label>
      <button type="submit">Login</button>
    </form>
    '''

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

########################
# ADMIN INTERFACE
########################
@app.route("/admin/legacy")
def admin_home():
    if not check_login():
        return redirect(url_for("login"))
        
    # Get some stats for the dashboard
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM news")
        news_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM birthdays")
        birthday_count = c.fetchone()[0]
        
        c.execute("SELECT value FROM settings WHERE key='weather_city'")
        city_row = c.fetchone()
        weather_city = city_row[0] if city_row else "Not configured"
        
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard - Digital Signage</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .stat-card {
                transition: all 0.3s ease;
                cursor: pointer;
            }
            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .stat-icon {
                font-size: 2.5em;
                opacity: 0.7;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/admin">Digital Signage Admin</a>
                <div class="navbar-nav">
                    <a class="nav-link active" href="/admin">Home</a>
                    <a class="nav-link" href="/admin/news">News</a>
                    <a class="nav-link" href="/admin/birthdays">Birthdays</a>
                    <a class="nav-link" href="/admin/settings">Settings</a>
                    <a class="nav-link" href="/logout">Logout</a>
                </div>
            </div>
        </nav>

        <div class="container mt-4">
            <h1 class="mb-4">Admin Dashboard</h1>
            
            <div class="row g-4">
                <div class="col-md-4">
                    <a href="/admin/news" class="text-decoration-none">
                        <div class="card stat-card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6 class="card-subtitle mb-2 text-muted">News Items</h6>
                                        <h2 class="card-title mb-0">{{news_count}}</h2>
                                    </div>
                                    <div class="stat-icon text-primary">
                                        <i class="fas fa-newspaper"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </a>
                </div>
                
                <div class="col-md-4">
                    <a href="/admin/birthdays" class="text-decoration-none">
                        <div class="card stat-card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6 class="card-subtitle mb-2 text-muted">Birthdays</h6>
                                        <h2 class="card-title mb-0">{{birthday_count}}</h2>
                                    </div>
                                    <div class="stat-icon text-warning">
                                        <i class="fas fa-birthday-cake"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </a>
                </div>
                
                <div class="col-md-4">
                    <a href="/admin/settings" class="text-decoration-none">
                        <div class="card stat-card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6 class="card-subtitle mb-2 text-muted">Weather Location</h6>
                                        <h5 class="card-title mb-0">{{weather_city}}</h5>
                                    </div>
                                    <div class="stat-icon text-info">
                                        <i class="fas fa-cloud-sun"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </a>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <a href="/admin/news" class="btn btn-primary">
                                    <i class="fas fa-plus"></i> Add News Item
                                </a>
                                <a href="/admin/birthdays" class="btn btn-warning">
                                    <i class="fas fa-plus"></i> Add Birthday
                                </a>
                                <a href="/admin/settings" class="btn btn-info">
                                    <i class="fas fa-cog"></i> Configure Weather
                                </a>
                                <a href="/" target="_blank" class="btn btn-success">
                                    <i class="fas fa-tv"></i> View Display
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Help & Information</h5>
                        </div>
                        <div class="card-body">
                            <h6>Getting Started</h6>
                            <ol>
                                <li>Configure your weather settings</li>
                                <li>Add some news items with images or GIFs</li>
                                <li>Add birthdays for your team</li>
                                <li>Open the display view in a full-screen browser</li>
                            </ol>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i> The display automatically updates
                                when you make changes in the admin panel.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(html, 
                                news_count=news_count,
                                birthday_count=birthday_count,
                                weather_city=weather_city)

@app.route("/admin/news", methods=["GET", "POST"])
def admin_news():
    if not check_login():
        return redirect(url_for("login"))
        
    message = ""
    message_type = "success"
    
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        if request.method == "POST":
            title = request.form.get("title")
            content = request.form.get("content")
            duration = request.form.get("duration", "10000")
            
            media_file = request.files.get('media')
            media_path = None
            
            if media_file and allowed_file(media_file.filename):
                processed_image, error = process_image(media_file)
                if error:
                    message = error
                    message_type = "danger"
                else:
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{media_file.filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(processed_image)
                    
                    media_path = f"/static/uploads/{filename}"
                    
                    c.execute(
                        "INSERT INTO news (title, content, media_path, duration) VALUES (?, ?, ?, ?)",
                        (title, content, media_path, duration)
                    )
                    conn.commit()
                    message = "News item added successfully!"
                    message_type = "success"
            else:
                message = "Please upload a valid image file (PNG, JPG, or GIF)"
                message_type = "danger"

        c.execute("""
            SELECT id, title, content, media_path, duration, created_at 
            FROM news 
            ORDER BY created_at DESC
        """)
        news_items = c.fetchall()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage News - Digital Signage</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .news-preview { max-width: 200px; max-height: 200px; object-fit: cover; }
            .news-card { transition: all 0.3s ease; }
            .news-card:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/admin">Digital Signage Admin</a>
                <div class="navbar-nav">
                    <a class="nav-link" href="/admin">Home</a>
                    <a class="nav-link active" href="/admin/news">News</a>
                    <a class="nav-link" href="/admin/birthdays">Birthdays</a>
                    <a class="nav-link" href="/admin/settings">Settings</a>
                    <a class="nav-link" href="/logout">Logout</a>
                </div>
            </div>
        </nav>

        <div class="container mt-4">
            <h1 class="mb-4">Manage News</h1>
            
            {% if message %}
            <div class="alert alert-{{message_type}} alert-dismissible fade show" role="alert">
                {{message}}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            {% endif %}

            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">Add New Item</h5>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input type="text" name="title" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Content</label>
                            <textarea name="content" class="form-control" rows="3" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Media (Image/GIF)</label>
                            <input type="file" name="media" class="form-control" accept=".jpg,.jpeg,.png,.gif" required>
                            <div class="form-text">
                                <strong>Recommended specifications:</strong><br>
                                • Ideal size: 1920x1080 pixels (16:9 aspect ratio)<br>
                                • Minimum size: 800x600 pixels<br>
                                • Maximum file size: 10MB<br>
                                • Supported formats: JPG, PNG, GIF<br>
                                • Images will be automatically optimized for display
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Duration (ms)</label>
                            <input type="number" name="duration" class="form-control" value="10000" min="1000" step="1000">
                            <div class="form-text">How long to display this item (in milliseconds)</div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add News Item</button>
                    </form>
                </div>
            </div>

            <h2 class="mb-3">Current News Items</h2>
            <div class="row row-cols-1 row-cols-md-2 g-4">
    {% for item in news_items %}
                <div class="col">
                    <div class="card h-100 news-card">
                        {% if item[3] %}
                        <img src="{{item[3]}}" class="card-img-top news-preview" alt="{{item[1]}}">
                        {% endif %}
                        <div class="card-body">
                            <h5 class="card-title">{{item[1]}}</h5>
                            <p class="card-text">{{item[2]}}</p>
                            <p class="card-text">
                                <small class="text-muted">
                                    Duration: {{item[4]}}ms<br>
                                    Created: {{item[5]}}
                                </small>
                            </p>
                            <a href="/admin/news/delete/{{item[0]}}" 
                               class="btn btn-danger btn-sm"
                               onclick="return confirm('Are you sure you want to delete this item?')">
                                <i class="fas fa-trash"></i> Delete
                            </a>
                        </div>
                    </div>
                </div>
    {% endfor %}
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(html, 
                                message=message,
                                message_type=message_type,
                                news_items=news_items)

@app.route("/admin/news/delete/<int:news_id>")
def admin_news_delete(news_id):
    if not check_login():
        return redirect(url_for("login"))
        
    try:
        # Delete from Firestore
        db.collection('news').document(str(news_id)).delete()
    except Exception as e:
        print(f"Error deleting news: {str(e)}")
    return redirect(url_for("admin_news"))

@app.route("/admin/birthdays", methods=["GET", "POST"])
def admin_birthdays():
    if not check_login():
        return redirect(url_for("login"))
        
    message = ""
    if request.method == "POST":
        try:
            name = request.form.get("name")
            birthdate = datetime.strptime(request.form.get("birthdate"), '%Y-%m-%d')
            sector = request.form.get("department")
            
            # Add to Firestore
            birthday_ref = db.collection('birthdays').document(name)
            birthday_ref.set({
                'date': birthdate,
                'sector': sector
            })
            message = "Birthday added successfully!"
        except Exception as e:
            message = f"Error adding birthday: {str(e)}"
    
    # Get birthdays from Firestore
    birthdays = get_upcoming_birthdays()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Birthdays - Digital Signage</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .birthday-card { transition: all 0.3s ease; }
            .birthday-card:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/admin">Digital Signage Admin</a>
                <div class="navbar-nav">
                    <a class="nav-link" href="/admin">Home</a>
                    <a class="nav-link" href="/admin/news">News</a>
                    <a class="nav-link active" href="/admin/birthdays">Birthdays</a>
                    <a class="nav-link" href="/admin/settings">Settings</a>
                    <a class="nav-link" href="/logout">Logout</a>
                </div>
            </div>
        </nav>

        <div class="container mt-4">
            <h1 class="mb-4">Manage Birthdays</h1>
            
            {% if message %}
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                {{message}}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            {% endif %}

            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">Add New Birthday</h5>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Name</label>
                            <input type="text" name="name" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Birthdate</label>
                            <input type="date" name="birthdate" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Department</label>
                            <input type="text" name="department" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Birthday</button>
                    </form>
                </div>
            </div>

            <h2 class="mb-3">Current Birthdays</h2>
            <div class="row row-cols-1 row-cols-md-3 g-4">
                {% for birthday in birthdays %}
                <div class="col">
                    <div class="card h-100 birthday-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <h5 class="card-title">{{birthday.name}}</h5>
                                <span class="badge bg-primary">{{birthday.sector}}</span>
                            </div>
                            <p class="card-text">
                                <i class="fas fa-calendar"></i> {{birthday.date}}
                            </p>
                            <a href="/admin/birthdays/delete/{{birthday.id}}" 
                               class="btn btn-danger btn-sm"
                               onclick="return confirm('Are you sure you want to delete this birthday?')">
                                <i class="fas fa-trash"></i> Delete
                            </a>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(html, message=message, birthdays=birthdays)

@app.route("/admin/birthdays/delete/<string:bd_id>")
def admin_birthdays_delete(bd_id):
    if not check_login():
        return redirect(url_for("login"))
    try:
        # Delete from Firestore
        db.collection('birthdays').document(bd_id).delete()
    except Exception as e:
        print(f"Error deleting birthday: {str(e)}")
    return redirect(url_for("admin_birthdays"))

@app.route("/")
def signage_display():
    """Main page - serve React app or fallback to data display"""
    # Check if React build exists
    react_build_path = os.path.join(DISPLAY_STATIC_DIR, "build", "index.html")

    if os.path.exists(react_build_path):
        print("Serving React build for main display")
        return send_from_directory(os.path.join(DISPLAY_STATIC_DIR, "build"), "index.html")

    # Fallback to original HTML template for backward compatibility
    print("\n=== Starting Signage Display Route (Legacy) ===")

    # Get display data using shared function
    weather, media_list, upcoming_birthdays, device_info, error = get_display_data()

    if error:
        print("No group configured - returning error page")
        return render_template_string("""
            <html>
                <body style="display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #000; color: #fff; font-family: sans-serif;">
                    <div style="text-align: center;">
                        <h1>Dispositivo não configurado</h1>
                        <p>Configure o dispositivo no painel administrativo.</p>
                    </div>
                </body>
            </html>
        """)

    print(f"Weather info retrieved: {'Success' if weather else 'Failed'}")
    print(f"Retrieved {len(upcoming_birthdays)} birthdays")
    print(f"Retrieved {len(media_list)} media items")

    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Digital Signage Display</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary-blue: #009FFF;
                --dark-blue: #0B5895;
                --darker-blue: #003B5C;
                --light-gray: #F0F3F5;
                --medium-gray: #C4CCD1;
                --dark-gray: #3A3A3A;
            }
            
            body {
                background: var(--light-gray);
                color: var(--dark-gray);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }
            
            .container-fluid {
                height: 100vh;
                padding: 2vh;
                display: flex;
                flex-direction: column;
            }
            
            .header {
                height: 15vh;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0 2vw;
                background: white;
                border-radius: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 2vh;
                gap: 2vw;
            }
            
            .company-logo {
                height: 10vh;
                object-fit: contain;
            }
            
            .datetime-container {
                display: flex;
                align-items: center;
                gap: 2vw;
                background: var(--light-gray);
                padding: 2vh 3vw;
                border-radius: 15px;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
                height: 12vh;
            }
            
            .time {
                font-size: 7.5vh;
                font-weight: bold;
                color: var(--dark-blue);
                line-height: 1;
                letter-spacing: -1px;
            }
            
            .date {
                font-size: 3.2vh;
                color: var(--dark-gray);
                line-height: 1.2;
                text-align: left;
            }
            
            .weather-widget {
                display: flex;
                align-items: center;
                gap: 2vw;
                background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
                padding: 1.5vh 2vw;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                color: white;
                height: 12vh;
                min-width: fit-content;
            }
            
            .weather-main {
                text-align: center;
                display: flex;
                align-items: center;
                gap: 1vw;
            }
            
            .weather-icon {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                padding: 0.5vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .weather-icon img {
                width: 7vh;
                height: 7vh;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
            }
            
            .temperature {
                font-size: 5vh;
                font-weight: bold;
                line-height: 1;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .weather-details {
                border-left: 2px solid rgba(255, 255, 255, 0.2);
                padding-left: 1.5vw;
                font-size: 2.2vh;
                display: grid;
                grid-template-columns: auto auto;
                gap: 1vh 2vw;
                align-items: center;
            }
            
            .weather-details div {
                white-space: nowrap;
                display: flex;
                align-items: center;
            }
            
            .weather-details i {
                width: 2vw;
                text-align: center;
                margin-right: 0.5vw;
                opacity: 0.9;
            }

            .main-content {
                flex: 1;
                display: flex;
                gap: 2vh;
                height: calc(83vh - 4vh); /* 100vh - header(15vh) - margins(2vh * 2) */
            }
            
            .news-container {
                flex: 1;
                position: relative;
                overflow: hidden;
                height: 100%;
            }
            
            .birthdays-container {
                width: 25vw;
                background: white;
                border-radius: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                padding: 2vh;
                display: flex;
                flex-direction: column;
                height: 100%;
            }
            
            .birthdays-title {
                font-size: 2.8vh;
                color: var(--dark-blue);
                margin-bottom: 1.5vh;
                padding-bottom: 0.8vh;
                border-bottom: 3px solid var(--primary-blue);
            }
            
            .birthday-list {
                flex: 1;
                overflow-y: hidden;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                gap: 1vh;
            }
            
            .birthday-item {
                background: var(--light-gray);
                padding: 1.2vh;
                border-radius: 10px;
                border-left: 4px solid var(--primary-blue);
                position: relative;
                height: calc((100% - 4vh) / 5);
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .birthday-item.today {
                background: linear-gradient(to right, 
                    rgba(255, 215, 0, 0.1),
                    var(--light-gray) 80%
                );
                border-left: 4px solid #FFD700;
            }
            
            .birthday-name {
                font-size: 2.2vh;
                font-weight: bold;
                color: var(--dark-blue);
                margin-bottom: 0.3vh;
            }
            
            .birthday-item.today .birthday-name {
                color: #FFD700;
            }
            
            .birthday-date {
                font-size: 1.8vh;
                color: var(--dark-gray);
            }
            
            .birthday-dept {
                font-size: 1.6vh;
                color: var(--dark-gray);
                font-style: italic;
            }
            
            .birthday-item.today::after {
                content: "🎉";
                position: absolute;
                right: 1.5vh;
                top: 50%;
                transform: translateY(-50%);
                font-size: 2.5vh;
                animation: celebrate 1s ease infinite;
            }
            
            @keyframes celebrate {
                0% { transform: translateY(-50%) rotate(0deg); }
                25% { transform: translateY(-50%) rotate(15deg); }
                75% { transform: translateY(-50%) rotate(-15deg); }
                100% { transform: translateY(-50%) rotate(0deg); }
            }

            .version-info {
                position: fixed;
                bottom: 0;
                right: 0;
                font-size: 14px;
                color: rgba(0, 0, 0, 0.3);
                background-color: rgba(255, 255, 255, 0.1);
                padding: 6px 10px;
                border-radius: 4px 0 0 0;
                backdrop-filter: blur(5px);
                -webkit-backdrop-filter: blur(5px);
                font-family: monospace;
                letter-spacing: 0.5px;
                box-shadow: -2px -2px 4px rgba(0, 0, 0, 0.1);
                transition: opacity 0.3s ease;
            }

            .version-info:hover {
                opacity: 0.8;
            }

            video {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }
        </style>
      </head>
      <body>
        <div class="container-fluid">
            <div class="header">
                <img src="/static/display/logo.png" alt="Company Logo" class="company-logo">
                
                <div class="datetime-container">
                    <div class="time" id="current-time"></div>
                    <div class="date" id="current-date"></div>
                </div>

                {% if weather %}
                <div class="weather-widget">
                    <div class="weather-main">
                        <div class="weather-icon">
                            <img src="http://openweathermap.org/img/wn/{{weather.icon}}@2x.png" alt="Weather">
                        </div>
                        <div class="temperature">{{weather.temperature}}°</div>
                    </div>
                    <div class="weather-details">
                        <div><i class="fas fa-temperature-high"></i> Máx: {{weather.temp_max}}°C</div>
                        <div><i class="fas fa-cloud-rain"></i> Chuva: {{weather.rain_chance}}%</div>
                        <div><i class="fas fa-temperature-low"></i> Mín: {{weather.temp_min}}°C</div>
                        <div><i class="fas fa-tint"></i> Umidade: {{weather.humidity}}%</div>
                    </div>
                </div>
                {% endif %}
            </div>

            <div class="main-content">
                <div class="news-container">
                    {% for media in media_list %}
                    <div class="media-slide" data-duration="{{media.duration}}" 
                         data-perfect-size="{{'true' if media.width == 1920 and media.height == 1080 else 'false'}}">
                        {% if media.is_video %}
                            <video src="{{ media.local_path }}" autoplay muted></video>
                        {% else %}
                            <img src="{{ media.local_path }}" alt="Display Content">
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                
                <div class="birthdays-container">
                    <div class="birthdays-title">
                        <i class="fas fa-birthday-cake"></i> Próximos Aniversários
                    </div>
                    <div class="birthday-list">
                        {% for birthday in upcoming_birthdays %}
                        <div class="birthday-item {% if birthday.is_today %}today{% endif %}">
                            <div class="birthday-name">{{birthday.name}}</div>
                            <div class="birthday-date">
                                {% if birthday.is_today %}
                                    Hoje! 🎂
                                {% else %}
                                    {% set bd = birthday.date.split('-') %}
                                    {{bd[2]}}/{{bd[1]}}
                                {% endif %}
                            </div>
                            <div class="birthday-dept">{{birthday.sector}}</div>
                        </div>
                        {% endfor %}
                    </div>
                    <div class="version-info">v{{ version }}</div>
                </div>
            </div>
        </div>

        <script>
            // Time and date update
            function updateDateTime() {
                const now = new Date();
                
                // Format time as HH:MM
                document.getElementById('current-time').textContent = 
                    now.toLocaleTimeString('pt-BR', { 
                        hour: '2-digit', 
                        minute: '2-digit',
                        hour12: false 
                    });
                
                // Format date as two lines: Weekday and Day Month
                const weekday = now.toLocaleDateString('pt-BR', { weekday: 'long' });
                const date = now.toLocaleDateString('pt-BR', { 
                    day: 'numeric',
                    month: 'long'
                });
                
                document.getElementById('current-date').innerHTML = 
                    `${weekday}<br>${date}`;
            }
            setInterval(updateDateTime, 1000);
            updateDateTime();

            // Media rotation
            const slides = document.querySelectorAll('.media-slide');
            let currentSlide = 0;
            let videoPlaying = false;
            let slideTimer = null;
            let isTransitioning = false;

            // Debug logging function
            function log(message) {
                const timestamp = new Date().toISOString().substr(11, 8);
                console.log(`[${timestamp}] ${message}`);
            }

            // Add CSS for smooth transitions
            const style = document.createElement('style');
            style.textContent = `
                .media-slide {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    opacity: 0;
                    transition: opacity 1s ease-in-out;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                
                .media-slide.active {
                    opacity: 1;
                }
                
                /* Default style for non-perfect size images */
                .media-slide:not([data-perfect-size="true"]) img,
                .media-slide:not([data-perfect-size="true"]) video {
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                    border-radius: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                
                /* Perfect size media (1920x1080) */
                .media-slide[data-perfect-size="true"] img,
                .media-slide[data-perfect-size="true"] video {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                
                /* Birthday styles */
                .birthday-item {
                    background: var(--light-gray);
                    margin-bottom: 1.5vh;
                    padding: 1.5vh;
                    border-radius: 10px;
                    border-left: 4px solid var(--primary-blue);
                    position: relative;
                }
                
                .birthday-item.today {
                    background: linear-gradient(to right, 
                        rgba(255, 215, 0, 0.1),
                        var(--light-gray) 80%
                    );
                    border-left: 4px solid #FFD700;
                }
                
                .birthday-item.today .birthday-name {
                    color: #FFD700;
                }
                
                .birthday-item.today::after {
                    content: "🎉";
                    position: absolute;
                    right: 1.5vh;
                    top: 50%;
                    transform: translateY(-50%);
                    font-size: 2.5vh;
                    animation: celebrate 1s ease infinite;
                }
                
                @keyframes celebrate {
                    0% { transform: translateY(-50%) rotate(0deg); }
                    25% { transform: translateY(-50%) rotate(15deg); }
                    75% { transform: translateY(-50%) rotate(-15deg); }
                    100% { transform: translateY(-50%) rotate(0deg); }
                }

                .version-info {
                    position: fixed;
                    bottom: 0;
                    right: 0;
                    font-size: 14px;
                    color: rgba(0, 0, 0, 0.3);
                    background-color: rgba(255, 255, 255, 0.1);
                    padding: 6px 10px;
                    border-radius: 4px 0 0 0;
                    backdrop-filter: blur(5px);
                    -webkit-backdrop-filter: blur(5px);
                    font-family: monospace;
                    letter-spacing: 0.5px;
                    box-shadow: -2px -2px 4px rgba(0, 0, 0, 0.1);
                    transition: opacity 0.3s ease;
                }

                .version-info:hover {
                    opacity: 0.8;
                }

                video {
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }
            `;
            document.head.appendChild(style);

            function showSlide(index) {
                log(`Attempting to show slide: ${index}. Current global slide index: ${currentSlide}. Total slides: ${slides.length}. isTransitioning: ${isTransitioning}`);
                if (isTransitioning && slides[index] !== slides[currentSlide]) { // Allow re-trigger for same slide if needed, but block new transitions
                    log('Transition already in progress for a different slide, ignoring showSlide call for new slide: ' + index);
                    return;
                }

                isTransitioning = true;
                log(`Starting transition TO slide ${index}. Setting isTransitioning = true.`);

                // Clear any existing timers
                if (slideTimer) {
                    log(`Clearing existing slideTimer for slide ${index}`);
                    clearTimeout(slideTimer);
                    slideTimer = null;
                }

                // Start fading out current active slide (if different from new slide)
                slides.forEach((slide, i) => {
                    if (slide.classList.contains('active') && i !== index) {
                        log(`Fading out currently active slide: ${i}`);
                        slide.classList.add('fade-out');
                    } else if (slide.classList.contains('active') && i === index) {
                        log(`Slide ${index} is already active. No fade out, will proceed to setup.`);
                    }
                });

                // Wait for fade out, then switch slides
                setTimeout(() => {
                    log(`Fade-out period ended for slide ${index}. Setting isTransitioning = false before content setup.`);
                    isTransitioning = false; 

                    // Hide all slides and stop all videos, then activate the target slide
                    slides.forEach((slide, i) => {
                        const isActiveTarget = (i === index);
                        if (slide.classList.contains('active') && !isActiveTarget) {
                            slide.classList.remove('active', 'fade-out');
                            log(`Deactivated slide: ${i}`);
                        }
                        const video = slide.querySelector('video');
                        if (video && !isActiveTarget) { // Only stop videos on non-target slides
                            log(`Stopping video on non-target slide ${i}`);
                            video.pause();
                            video.currentTime = 0;
                            video.onended = null;
                            video.ontimeupdate = null;
                            video.onloadedmetadata = null;
                            video.removeAttribute('data-transitioning-next');
                        }
                    });

                    // Show and setup current slide
                    const currentElement = slides[index];
                    if (!currentElement) {
                        log(`ERROR: currentElement for slide index ${index} is undefined! Total slides: ${slides.length}`);
                        // Attempt to recover or bail
                        if (slides.length > 0) {
                             log(`ERROR: Attempting to recover by going to slide 0`);
                             currentSlide = 0; // Reset to a known good state
                             nextSlide(); // This will call showSlide(0)
                        }
                        return;
                    }
                    
                    log(`Activating slide ${index}. Element: ${currentElement.tagName}`);
                    currentElement.classList.remove('fade-out'); // Ensure it's not faded out if it was the same slide
                    currentElement.classList.add('active');
                    
                    const video = currentElement.querySelector('video');
                    if (video) {
                        log(`Setting up video on slide ${index}. Video src: ${video.src}`);
                        videoPlaying = true;
                        video.dataset.transitioningNext = 'false';

                        const handleVideoEnd = (reason) => {
                            log(`handleVideoEnd called for slide: ${index} (src: ${video.src.split('/').pop()}) due to: ${reason}. Current global slide: ${currentSlide}. Video transitioningNext: ${video.dataset.transitioningNext}`);
                            if (video.dataset.transitioningNext === 'true') {
                                log(`Transition for video ${index} already triggered. Ignoring.`);
                                return;
                            }
                            video.dataset.transitioningNext = 'true';
                            log(`Set transitioningNext=true for video ${index}`);

                            // Clear handlers and timer
                            video.ontimeupdate = null;
                            video.onended = null;
                            video.onloadedmetadata = null;
                            if (slideTimer) {
                                log(`Clearing slideTimer in handleVideoEnd for slide ${index}`);
                                clearTimeout(slideTimer);
                                slideTimer = null;
                            }
                            
                            videoPlaying = false;
                            nextSlide();
                        };

                        video.onloadedmetadata = () => {
                            log(`Video metadata loaded for slide ${index} (src: ${video.src.split('/').pop()}). Duration: ${video.duration}, readyState: ${video.readyState}`);
                            if (slideTimer) {
                                log(`Clearing pre-existing slideTimer in onloadedmetadata for slide ${index}`);
                                clearTimeout(slideTimer);
                                slideTimer = null;
                            }
                            
                            const durationMs = video.duration * 1000;
                            if (isFinite(durationMs) && durationMs > 0) {
                                log(`Setting safety timeout for ${durationMs}ms for slide ${index}`);
                                slideTimer = setTimeout(() => handleVideoEnd('safety_timeout'), durationMs);
                            } else {
                                log(`Invalid duration for video ${index}: ${video.duration}. Safety timeout not set or using fallback. Will rely on 'onended'.`);
                            }
                        };
                        
                        video.onended = () => handleVideoEnd('ended_event');
                        video.onerror = (e) => {
                            log(`ERROR on video element for slide ${index} (src: ${video.src.split('/').pop()}): ${JSON.stringify(e)} MediaError: ${JSON.stringify(video.error)}`);
                            handleVideoEnd('video_element_error');
                        };
                        
                        log(`Attempting to play video for slide ${index} (src: ${video.src.split('/').pop()})`);
                        video.play().then(() => {
                            log(`Video started playing on slide ${index} (src: ${video.src.split('/').pop()}). Setting isTransitioning = false.`);
                            isTransitioning = false; 
                        }).catch(error => {
                            log(`Error playing video on slide ${index} (src: ${video.src.split('/').pop()}): ${error}. isTransitioning state: ${isTransitioning}`);
                            handleVideoEnd('play_error');
                        });

                        if (video.readyState >= 2 && isFinite(video.duration)) {
                           log(`Video ${index} metadata already available on setup. Manually triggering onloadedmetadata.`);
                           video.onloadedmetadata();
                        } else {
                            log(`Video ${index} metadata not yet available (readyState: ${video.readyState}, duration: ${video.duration}). Waiting for event.`);
                        }

                    } else { // Image slide
                        log(`Setting up image on slide ${index}. Setting isTransitioning = false.`);
                        videoPlaying = false;
                        const duration = parseInt(currentElement.dataset.duration);
                        if (slideTimer) { // Clear previous timer just in case
                            log(`Clearing existing slideTimer for image slide ${index}`);
                            clearTimeout(slideTimer);
                        }
                        slideTimer = setTimeout(() => {
                            log(`Image slide ${index} timer expired. Calling nextSlide.`);
                            nextSlide();
                        }, Math.max(duration - 1000, 1000)); 
                        isTransitioning = false;
                    }
                }, 1000); // Wait for fade out animation (1s)
            }

            function nextSlide() {
                const oldSlide = currentSlide;
                log(`nextSlide called. Old currentSlide: ${oldSlide}. isTransitioning: ${isTransitioning}`);
                if (isTransitioning) {
                    log('Transition already in progress, ignoring nextSlide call from old slide ' + oldSlide);
                    return;
                }

                currentSlide = (currentSlide + 1) % slides.length;
                log(`nextSlide: New currentSlide calculated: ${currentSlide}. Total slides: ${slides.length}. About to call showSlide(${currentSlide}).`);
                showSlide(currentSlide);
            }

            if (slides.length > 0) {
                log(`Starting slideshow with ${slides.length} slides`);
                showSlide(0);
            } else {
                log('No slides found');
            }

            // Reload page every hour to ensure fresh content
            setTimeout(() => {
                log('Triggering hourly page reload');
                window.location.reload();
            }, 3600000);
        </script>
      </body>
    </html>
    """
    
    return render_template_string(html, 
                                weather=weather,
                                media_list=media_list,
                                upcoming_birthdays=upcoming_birthdays,
                                version=VERSION)

# React build serving routes
@app.route('/static/build/<path:filename>')
def serve_react_build(filename):
    """Serve React build static files"""
    build_dir = os.path.join(DISPLAY_STATIC_DIR, "build")
    return send_from_directory(build_dir, filename)

@app.route('/admin')
@app.route('/admin/<path:path>')
def admin_react(path=''):
    """Serve React app for admin routes"""
    react_build_path = os.path.join(DISPLAY_STATIC_DIR, "build", "index.html")

    if os.path.exists(react_build_path):
        print("Serving React build for admin interface")
        return send_from_directory(os.path.join(DISPLAY_STATIC_DIR, "build"), "index.html")

    # Fallback to legacy admin route
    return redirect('/admin/legacy')

@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not check_login():
        return redirect(url_for("login"))
        
    message = ""
    if request.method == "POST":
        try:
            # Update Firestore settings
            settings_ref = db.collection('config').document('openWeather')
            settings_ref.set({
                'apiKey': request.form.get("weather_api_key"),
                'location': request.form.get("weather_city")
            })
            message = "Settings updated successfully!"
        except Exception as e:
            message = f"Error updating settings: {str(e)}"
    
    # Get current settings
    settings_doc = db.collection('config').document('openWeather').get()
    settings = settings_doc.to_dict() if settings_doc.exists else {}
    api_key = settings.get('apiKey', '')
    city = settings.get('location', '')

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Settings - Digital Signage</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>Settings</h1>
            
            {% if message %}
            <div class="alert alert-success">{{message}}</div>
            {% endif %}
            
            <form method="POST">
                <div class="mb-3">
                    <label>OpenWeatherMap API Key</label>
                    <input type="text" name="weather_api_key" class="form-control" 
                           value="{{api_key}}" required>
                </div>
                <div class="mb-3">
                    <label>Weather City</label>
                    <input type="text" name="weather_city" class="form-control" 
                           value="{{city}}" required>
                </div>
                <button type="submit" class="btn btn-primary">Save Settings</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, 
                                message=message, 
                                api_key=api_key or '', 
                                city=city or '')

# Initialize Oracle after other initializations
try:
    initialize_oracle()
except Exception as e:
    print(f"Warning: Oracle initialization failed: {str(e)}")

########################
# API ROUTES
########################

def get_display_data():
    """Extract display data logic for reuse in both HTML and API routes"""
    # Get weather info from OpenWeatherMap
    weather = get_weather_info()

    # Get device info from device manager
    device_info = None
    if device_manager.device_doc:
        device_info = {
            'type': device_manager.device_doc.get('type', 'display_tv'),
            'name': device_manager.device_doc.get('name', ''),
            'description': device_manager.device_doc.get('description', ''),
            'id': device_manager.device_doc.get('id', ''),
        }

    # Get group data from Firebase
    current_group = cache_manager.get_cached_group()

    if not current_group:
        return None, None, None, device_info, "Device not configured"

    # Get upcoming birthdays
    upcoming_birthdays = get_upcoming_birthdays()

    media_list = current_group.get('media', [])

    # Map cloud media to local paths
    for media in media_list:
        content_type = media.get('type', 'image/jpeg')

        # Determine correct file extension based on content type
        if content_type.startswith('video/') or content_type == 'video':
            content_type_to_ext = {
                'video/mp4': '.mp4',
                'video/webm': '.webm',
                'video/quicktime': '.mov',
                'video': '.mp4'  # Default for generic video type
            }
            extension = content_type_to_ext.get(content_type, '.mp4')
        else:
            # For images, try to get extension from URL first, fallback to mime type
            extension = os.path.splitext(media.get('url', ''))[1]
            if not extension or extension == '.jpe':
                extension = mimetypes.guess_extension(content_type) or '.jpg'
                if extension == '.jpe':
                    extension = '.jpg'

        local_path = os.path.join(MEDIA_FOLDER, f"{media['id']}{extension}")
        media['local_path'] = f"/static/media/{media['id']}{extension}"

        # Handle duration based on media type
        if content_type.startswith('video/') or content_type == 'video':
            # For videos, set duration to -1 to indicate "play until end"
            media['duration'] = -1
            media['is_video'] = True
        else:
            # For images, use specified duration or default to 10 seconds
            try:
                duration = media.get('duration')
                media['duration'] = int(duration) * 1000 if duration is not None else 10000
            except (ValueError, TypeError):
                media['duration'] = 10000  # Default to 10 seconds if invalid duration
            media['is_video'] = False

        # Get dimensions if media exists locally
        if os.path.exists(local_path):
            try:
                if content_type.startswith('image/'):
                    with Image.open(local_path) as img:
                        media['width'], media['height'] = img.size
                elif content_type.startswith('video/') or content_type == 'video':
                    # Default video dimensions for now
                    media['width'] = 1920
                    media['height'] = 1080
            except Exception as e:
                print(f"Error getting media dimensions: {str(e)}")
                media['width'] = 1920
                media['height'] = 1080

    return weather, media_list, upcoming_birthdays, device_info, None

@app.route("/api/v1/display")
def api_display_data():
    """API endpoint for main display data"""
    weather, media_list, upcoming_birthdays, device_info, error = get_display_data()

    if error:
        return jsonify({
            'error': error,
            'configured': False,
            'device': device_info
        }), 400

    return jsonify({
        'weather': weather,
        'media': media_list,
        'birthdays': upcoming_birthdays,
        'device': device_info,
        'version': VERSION,
        'configured': True
    })

@app.route("/api/v1/weather")
def api_weather():
    """API endpoint for weather data only"""
    weather = get_weather_info()
    return jsonify({'weather': weather})

@app.route("/api/v1/birthdays")
def api_birthdays():
    """API endpoint for birthday data only"""
    birthdays = get_upcoming_birthdays()
    return jsonify({'birthdays': birthdays})

@app.route("/api/v1/media")
def api_media():
    """API endpoint for media data only"""
    current_group = cache_manager.get_cached_group()
    if not current_group:
        return jsonify({'error': 'Device not configured', 'media': []}), 400

    media_list = current_group.get('media', [])

    # Process media list (same logic as in get_display_data)
    for media in media_list:
        content_type = media.get('type', 'image/jpeg')

        if content_type.startswith('video/') or content_type == 'video':
            content_type_to_ext = {
                'video/mp4': '.mp4',
                'video/webm': '.webm',
                'video/quicktime': '.mov',
                'video': '.mp4'
            }
            extension = content_type_to_ext.get(content_type, '.mp4')
        else:
            extension = os.path.splitext(media.get('url', ''))[1]
            if not extension or extension == '.jpe':
                extension = mimetypes.guess_extension(content_type) or '.jpg'
                if extension == '.jpe':
                    extension = '.jpg'

        local_path = os.path.join(MEDIA_FOLDER, f"{media['id']}{extension}")
        media['local_path'] = f"/static/media/{media['id']}{extension}"

        if content_type.startswith('video/') or content_type == 'video':
            media['duration'] = -1
            media['is_video'] = True
        else:
            try:
                duration = media.get('duration')
                media['duration'] = int(duration) * 1000 if duration is not None else 10000
            except (ValueError, TypeError):
                media['duration'] = 10000
            media['is_video'] = False

        if os.path.exists(local_path):
            try:
                if content_type.startswith('image/'):
                    with Image.open(local_path) as img:
                        media['width'], media['height'] = img.size
                elif content_type.startswith('video/') or content_type == 'video':
                    media['width'] = 1920
                    media['height'] = 1080
            except Exception as e:
                print(f"Error getting media dimensions: {str(e)}")
                media['width'] = 1920
                media['height'] = 1080

    return jsonify({'media': media_list})

@app.route("/api/v1/admin/news", methods=["GET"])
def api_admin_news():
    """API endpoint for admin news data"""
    if not check_login():
        return jsonify({'error': 'Authentication required'}), 401

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, title, content, media_path, duration, created_at
            FROM news
            ORDER BY created_at DESC
        """)
        news_items = c.fetchall()

    # Convert to list of dicts
    news_list = []
    for item in news_items:
        news_list.append({
            'id': item[0],
            'title': item[1],
            'content': item[2],
            'media_path': item[3],
            'duration': item[4],
            'created_at': item[5]
        })

    return jsonify({'news': news_list})

@app.route("/api/v1/admin/settings", methods=["GET"])
def api_admin_settings():
    """API endpoint for admin settings data"""
    if not check_login():
        return jsonify({'error': 'Authentication required'}), 401

    # Get current settings from Firestore
    settings_doc = db.collection('config').document('openWeather').get()
    settings = settings_doc.to_dict() if settings_doc.exists else {}

    return jsonify({
        'weather': {
            'apiKey': settings.get('apiKey', ''),
            'location': settings.get('location', '')
        }
    })


@app.route("/test/birthdays")
def test_birthdays():
    """Test route to check birthday data"""
    print("\n=== Testing Birthday Route ===")
    birthdays = get_upcoming_birthdays()
    return jsonify({
        'count': len(birthdays),
        'birthdays': birthdays
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
