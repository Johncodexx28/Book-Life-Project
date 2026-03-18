import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from models import db, User, MemoryImage
from datetime import datetime
from functools import wraps
import re
import click


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///book_life.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration for image uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Utility function for admin check
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ================= ROUTES =================

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('bookshelf'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('bookshelf'))
        
    if request.method == 'POST':
       
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
      
        if not email or len(email) > 120 or not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            flash('Invalid email format provided.', 'danger')
            return render_template('login.html')
            
        if not password or len(password) < 8 or len(password) > 128:
            flash('Invalid password length.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Welcome back to your Memory Shelf 💕', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('bookshelf'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('bookshelf'))
        
    if request.method == 'POST':
     
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
       
        if not email or len(email) > 120 or not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            flash('Invalid email format provided.', 'danger')
            return render_template('register.html')
            
        if not password or len(password) < 8 or len(password) > 128:
            flash('Password must be between 8 and 128 characters.', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Account already exists with this email.', 'danger')
            return redirect(url_for('login'))
            
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(email=email, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/bookshelf')
@login_required
def bookshelf():
    
    years = db.session.query(MemoryImage.year).filter_by(user_id=current_user.id).distinct().all()
    years = [y[0] for y in years]
    
   
    if not years:
        years = [datetime.now().year]
        
    years.sort()
    return render_template('bookshelf.html', years=years)

@app.route('/year/<int:year>')
@login_required
def year_view(year):
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
   
    images = MemoryImage.query.filter_by(user_id=current_user.id, year=year).all()
    
   
    images_by_month = {month_num: [] for month_num, _ in months}
    for img in images:
        if img.month in images_by_month:
            images_by_month[img.month].append(img)
            
    return render_template('year.html', year=year, months=months, images_by_month=images_by_month)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.referrer or url_for('bookshelf'))
        
    file = request.files['file']
    year = request.form.get('year', type=int)
    month = request.form.get('month', type=int)
    
    if not year or not month:
        flash('Year and Month required', 'danger')
        return redirect(request.referrer or url_for('bookshelf'))
        
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('year_view', year=year))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.id}_{year}_{month}_{int(datetime.now().timestamp())}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(os.path.join(app.root_path, file_path))
        
        # Save to database
        new_image = MemoryImage(user_id=current_user.id, year=year, month=month, filename=filename)
        db.session.add(new_image)
        db.session.commit()
        
        flash('Memory added successfully! ✨', 'success')
        
    return redirect(url_for('year_view', year=year))


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_memories = MemoryImage.query.count()
    
    # Calculate total storage used in the uploads folder
    total_storage_bytes = 0
    upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    if os.path.exists(upload_path):
        for f in os.listdir(upload_path):
            file_path = os.path.join(upload_path, f)
            if os.path.isfile(file_path):
                total_storage_bytes += os.path.getsize(file_path)
    
    # Convert bytes to human-readable format
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if total_storage_bytes < 1024.0:
            total_storage_size = f"{total_storage_bytes:.1f} {x}"
            break
        total_storage_bytes /= 1024.0
    else:
        total_storage_size = f"{total_storage_bytes:.1f} PB"
        
    return render_template('admin/dashboard.html', total_users=total_users, total_memories=total_memories, total_storage_size=total_storage_size)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    # Need to pass memory count per user or calculate it in the template
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin_users'))
        
    user = User.query.get_or_404(user_id)
    
    # Delete all associated images from the filesystem
    for image in user.images:
        file_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
                
    # The associated MemoryImages should ideally be cascaded or deleted here. 
    # Since we didn't specify cascade="all, delete-orphan", we must delete them manually:
    MemoryImage.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f"User {user.email} and all their memories have been deleted.", "success")
    return redirect(url_for('admin_users'))

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")

@app.cli.command("upgrade-db")
def upgrade_db():
    import sqlite3
    db_path = os.path.join(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), 'book_life.db') # basic extraction for sqlite filepath
    # Assuming relative path from the root
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if db_path.startswith('/'): # absolute
            pass
        else: # relative
           db_path = os.path.join(app.root_path, db_path)

    try:
        conn = sqlite3.connect('instance/book_life.db') # Assuming standard Flask-SQLAlchemy instance folder
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;")
        conn.commit()
        conn.close()
        print("Database upgraded successfully: 'is_admin' column added.")
    except Exception as e:
        print(f"Error upgrading database: {e}")

@app.cli.command("make-admin")
@click.argument("email")
def make_admin(email):
    # This needs to run in the app context, which CLI commands do by default
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"Success! {email} is now an admin.")
    else:
        print(f"Error: User with email {email} not found.")

if __name__ == '__main__':
    app.run(debug=True)
