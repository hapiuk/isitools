from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_migrate import Migrate
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import os
import smtplib
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key

# Configure the SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'static', 'db', 'isitools.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)  # Initialize Flask-Mail
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Initialize the LoginManager
# Initialize the LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login page if not authenticated

# User model for authentication
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    department = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    access_level = db.Column(db.String(50), nullable=False, default='User')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Contact model
class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    contact_number = db.Column(db.String(50), nullable=False)

# Email Settings model
class EmailSettings(db.Model):
    __tablename__ = 'email_settings'
    id = db.Column(db.Integer, primary_key=True)
    mail_server = db.Column(db.String(150), nullable=False)
    mail_port = db.Column(db.Integer, nullable=False)
    email_username = db.Column(db.String(150), nullable=False)
    email_password = db.Column(db.String(150), nullable=False)
    use_tls = db.Column(db.Boolean, nullable=False)
    use_ssl = db.Column(db.Boolean, nullable=False)
    default_sender_name = db.Column(db.String(150), nullable=False)
    default_sender_email = db.Column(db.String(150), nullable=False)

# Function to send emails
def send_user_email(to_address, subject, body):
    settings = EmailSettings.query.first()

    if not settings:
        flash("Email settings are not configured properly in the database.", "error")
        return

    try:
        # Set up the SMTP server using settings from the database
        server = smtplib.SMTP(settings.mail_server, settings.mail_port)
        if settings.use_tls:
            server.starttls()
        server.login(settings.email_username, settings.email_password)

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = f"{settings.default_sender_name} <{settings.default_sender_email}>"
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        server.send_message(msg)
        server.quit()
        flash('Email sent successfully.', 'success')
    except Exception as e:
        flash(f"Failed to send email: {e}", "error")

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()  # This will create the email_settings table if it doesn't exist

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Ensure 'email' and 'password' keys exist in the form
        if 'email' not in request.form or 'password' not in request.form:
            flash('Missing email or password.', 'error')
            return redirect(url_for('login'))

        email = request.form['email']
        password = request.form['password']

        # Find the user by email
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Route for logging out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Route for the dashboard (home page)
@app.route('/')
@login_required
def dashboard():
    # Example email settings (you can fetch these from your config or database)
    email_settings = EmailSettings.query.first()
    return render_template('dashboard.html', email_settings=email_settings)

# Route to process PUWER reports
@app.route('/process_puwer_reports', methods=['POST'])
@login_required
def process_puwer_reports():
    site_name = request.form['site_name']
    report_files = request.files.getlist('report_files')

    # Implement your logic to process the PUWER reports here

    flash('PUWER reports processed successfully.', 'success')
    return redirect(url_for('dashboard'))

# Route to process LOLER reports
@app.route('/process_loler_reports', methods=['POST'])
@login_required
def process_loler_reports():
    site_name = request.form['site_name']
    report_files = request.files.getlist('report_files')

    # Implement your logic to process the LOLER reports here

    flash('LOLER reports processed successfully.', 'success')
    return redirect(url_for('dashboard'))

# Route to process AECOM reports
@app.route('/process_aecom_reports', methods=['POST'])
@login_required
def process_aecom_reports():
    business_entity = request.form['business_entity']
    report_files = request.files.getlist('report_files')

    # Implement your logic to process the AECOM reports here

    flash('AECOM reports processed successfully.', 'success')
    return redirect(url_for('dashboard'))

# Function to generate a random password
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

# Route to create a new user
@app.route('/create_user', methods=['POST'])
@login_required
def create_user():
    if current_user.access_level != 'Admin':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('dashboard'))

    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    department = request.form['department']
    location = request.form['location']
    access_level = request.form['access_level']

    # Generate a random password
    password = generate_random_password()

    # Check if the user already exists
    if User.query.filter_by(email=email).first():
        flash('User with that email already exists.', 'error')
        return redirect(url_for('dashboard'))

    # Create a new user object
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        department=department,
        location=location,
        access_level=access_level
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Send the email to the user
    subject = "Your New Account Details"
    body = f"Hello {first_name},\n\nYour account has been created. Your password is: {password}\nPlease change it upon your first login."
    try:
        send_user_email(email, subject, body)
        flash('New user created successfully and email sent.', 'success')
    except Exception as e:
        flash(f'User created but failed to send email: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/email_settings', methods=['POST'])
@login_required
def email_settings():
    if current_user.access_level != 'Admin':
        return jsonify({'status': 'error', 'message': 'You do not have permission to perform this action.'}), 403

    # Fetch the current email settings record or create a new one if none exists
    settings = EmailSettings.query.first()
    if not settings:
        settings = EmailSettings()

    # Update settings based on form data
    settings.mail_server = request.form.get('mail_server', settings.mail_server)
    settings.mail_port = int(request.form.get('mail_port', settings.mail_port))
    settings.email_username = request.form.get('email_username', settings.email_username)
    settings.email_password = request.form.get('email_password', settings.email_password)
    settings.use_tls = request.form.get('use_tls', 'false').lower() == 'true'
    settings.use_ssl = request.form.get('use_ssl', 'false').lower() == 'true'
    settings.default_sender_name = request.form.get('default_sender_name', settings.default_sender_name)
    settings.default_sender_email = request.form.get('default_sender_email', settings.default_sender_email)

    try:
        # Add to session if it's a new record
        if not settings.id:
            db.session.add(settings)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Email settings updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error saving email settings: {str(e)}'}), 500

# Route to handle email settings updates
@app.route('/update_email_settings', methods=['POST'])
@login_required
def update_email_settings():
    if current_user.access_level != 'Admin':
        return jsonify({'status': 'error', 'message': 'You do not have permission to perform this action.'}), 403

    field = request.form.get('field')
    value = request.form.get('value')
    settings = EmailSettings.query.first()

    if not settings:
        return jsonify({'status': 'error', 'message': 'Email settings not found.'}), 404

    try:
        # Map fields correctly to settings attributes
        if field == 'mail_server':
            settings.mail_server = value
        elif field == 'mail_port':
            settings.mail_port = int(value)
        elif field == 'email_username':
            settings.email_username = value
        elif field == 'email_password':
            settings.email_password = value
        elif field == 'use_tls':
            settings.use_tls = value.lower() == 'true'
        elif field == 'use_ssl':
            settings.use_ssl = value.lower() == 'true'
        elif field == 'default_sender_name':
            settings.default_sender_name = value
        elif field == 'default_sender_email':
            settings.default_sender_email = value
        else:
            return jsonify({'status': 'error', 'message': 'Invalid field.'}), 400

        db.session.commit()  # Commit the changes to the database
        return jsonify({'status': 'success', 'message': f'{field.replace("_", " ").title()} updated successfully!'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Route to test email settings
@app.route('/test_email_settings', methods=['POST'])
@login_required
def test_email_settings():
    if current_user.access_level != 'Admin':
        return jsonify({'status': 'error', 'message': 'You do not have permission to perform this action.'}), 403

    # Fetch current email settings from the database
    settings = EmailSettings.query.first()

    if not settings:
        return jsonify({'status': 'error', 'message': 'Email settings not configured properly.'}), 404

    # Display current email settings in the flash message for debugging
    email_info = {
        'mail_server': settings.mail_server,
        'mail_port': settings.mail_port,
        'email_username': settings.email_username,
        'use_tls': settings.use_tls,
        'use_ssl': settings.use_ssl,
        'default_sender_name': settings.default_sender_name,
        'default_sender_email': settings.default_sender_email
    }

    # Send test email
    try:
        send_user_email('aaron.gomm@outlook.com', 'Test Email', 'This is a test email to verify settings.')
        return jsonify({'status': 'success', 'settings': email_info})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to send test email: {e}'}), 500
        
# Route to update user profile
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    field = request.form.get('field')
    value = request.form.get('value')

    # Update the user's profile based on the field
    if field and value:
        if field == 'firstName':
            current_user.first_name = value
        elif field == 'lastName':
            current_user.last_name = value
        elif field == 'email':
            if User.query.filter_by(email=value).first():
                return jsonify({'status': 'error', 'message': 'Email is already in use by another account.'})
            current_user.email = value
        elif field == 'department':
            current_user.department = value
        elif field == 'location':
            current_user.location = value
        else:
            return jsonify({'status': 'error', 'message': 'Invalid field.'})

        db.session.commit()
        return jsonify({'status': 'success', 'message': f'{field.capitalize()} updated successfully!'})

    return jsonify({'status': 'error', 'message': 'Missing field or value.'})

# Route to create a new contact
@app.route('/create_contact', methods=['POST'])
@login_required
def create_contact():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    contact_number = request.form['contact_number']

    # Check if the contact already exists
    if Contact.query.filter_by(email=email).first():
        flash('Contact with that email already exists.', 'error')
        return redirect(url_for('dashboard'))

    # Create a new contact object
    new_contact = Contact(
        first_name=first_name,
        last_name=last_name,
        email=email,
        contact_number=contact_number
    )
    db.session.add(new_contact)
    db.session.commit()

    flash('New contact created successfully.', 'success')
    return redirect(url_for('dashboard'))

# Route to get users as JSON (for API)
@app.route('/api/users')
@login_required
def api_get_users():
    if current_user.access_level != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Query users with pagination
    users = User.query.paginate(page=page, per_page=per_page)
    user_list = [
        {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'department': user.department,
            'location': user.location,
            'access_level': user.access_level
        } for user in users.items
    ]

    return jsonify({
        'users': user_list,
        'total': users.total,
        'pages': users.pages,
        'current_page': users.page
    })

# Route to delete a user
@app.route('/api/user/<int:user_id>', methods=['DELETE'])
@login_required
def api_delete_user(user_id):
    if current_user.access_level != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': 'User deleted'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# Route to get contacts as JSON (for API) with pagination
@app.route('/api/contacts')
@login_required
def api_get_contacts():
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Query contacts with pagination
    contacts = Contact.query.paginate(page=page, per_page=per_page)
    contact_list = [
        {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': contact.email,
            'contact_number': contact.contact_number
        } for contact in contacts.items
    ]

    return jsonify({
        'contacts': contact_list,
        'total': contacts.total,
        'pages': contacts.pages,
        'current_page': contacts.page
    })

# Route to delete a contact
@app.route('/api/contact/<int:contact_id>', methods=['DELETE'])
@login_required
def api_delete_contact(contact_id):
    if current_user.access_level != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    contact = Contact.query.get(contact_id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'success': 'Contact deleted'}), 200
    else:
        return jsonify({'error': 'Contact not found'}), 404

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Run the application
if __name__ == '__main__':
    # Set debug to True for development; remember to set it to False in production
    app.run(debug=True)
