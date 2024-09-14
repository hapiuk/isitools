from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_migrate import Migrate
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
import smtplib
import random
import string
import requests
import base64
import logging
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logging.basicConfig(level=logging.DEBUG)

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
    reset_token = db.Column(db.String(256), nullable=True)  # Add this line
    reset_token_expiration = db.Column(db.DateTime, nullable=True)  # Optional for token expiration

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

class EmailSettings(db.Model):
    __tablename__ = 'email_settings'
    id = db.Column(db.Integer, primary_key=True)
    mail_server = db.Column(db.String(150), nullable=False)
    mail_port = db.Column(db.Integer, nullable=False)
    email_username = db.Column(db.String(150), nullable=False)  # Keep this for 'From' address
    oauth_client_id = db.Column(db.String(150), nullable=True)
    oauth_tenant_id = db.Column(db.String(150), nullable=True)
    oauth_client_secret = db.Column(db.String(150), nullable=True)
    use_tls = db.Column(db.Boolean, nullable=False)
    use_ssl = db.Column(db.Boolean, nullable=False)
    default_sender_name = db.Column(db.String(150), nullable=False)
    default_sender_email = db.Column(db.String(150), nullable=False)
    oauth_scope = db.Column(db.String(150), default='https://graph.microsoft.com/.default')

def get_oauth_token():
    settings = EmailSettings.query.first()
    
    if not settings or not settings.oauth_client_id or not settings.oauth_client_secret or not settings.oauth_tenant_id:
        flash("OAuth settings are not configured properly in the database.", "error")
        return None
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': settings.oauth_client_id,
        'client_secret': settings.oauth_client_secret,
        'scope': 'https://graph.microsoft.com/.default',  # Application permission scope
    }

    token_url = f'https://login.microsoftonline.com/{settings.oauth_tenant_id}/oauth2/v2.0/token'

    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        tokens = response.json()
        return tokens['access_token']
    except requests.exceptions.RequestException as e:
        error_content = response.content.decode() if response else 'No response content'
        flash(f"Failed to retrieve OAuth token: {e}. Response content: {error_content}", "error")
        print(f"Error retrieving OAuth token: {e}. Response content: {error_content}")
        return None

def send_user_email(to_address, subject, password):
    settings = EmailSettings.query.first()

    if not settings:
        flash("Email settings are not configured properly in the database.", "error")
        return False

    try:
        token = get_oauth_token()
        if not token:
            return False

        # Correct path to the logo image
        logo_path = os.path.join(BASE_DIR, 'static', 'images', 'logos', 'Logo.png')
        logging.debug(f"Attempting to load logo from path: {logo_path}")

        # Load and encode the logo image
        try:
            with open(logo_path, 'rb') as logo_file:
                logo_data = base64.b64encode(logo_file.read()).decode('utf-8')
        except FileNotFoundError:
            error_message = f"Logo file not found at {logo_path}. Please check the file path."
            flash(error_message, "error")
            logging.error(error_message)
            logo_data = ''  # Skip the logo if not found

        # Set up the Graph API endpoint for sending mail
        sender_email = settings.default_sender_email
        graph_api_url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"

        # Prepare the HTML content of the email
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="text-align: center;">
                <img src="data:image/png;base64,{logo_data}" alt="ISI Tools Logo" style="max-width: 200px; margin-bottom: 20px;">
            </div>
            <p>Dear User,</p>
            <p>Your account has been created successfully. Here are your login details:</p>
            <ul>
                <li><strong>Email:</strong> {to_address}</li>
                <li><strong>Password:</strong> {password}</li>
            </ul>
            <p>You can log in using the following link:</p>
            <p><a href="http://isitools.local:5000" style="color: #0F70B7; text-decoration: none;">Login to ISI Tools</a></p>
            <p>Best regards,<br>ISI Tools Admin</p>
        </body>
        </html>
        """

        # Prepare the email payload
        email_message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_content
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_address
                        }
                    }
                ],
                "from": {
                    "emailAddress": {
                        "address": settings.default_sender_email
                    }
                }
            },
            "saveToSentItems": "true"
        }

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Send the request to the Graph API
        response = requests.post(graph_api_url, json=email_message, headers=headers)

        # Log response details for debugging
        logging.debug(f"Response status: {response.status_code}, Response content: {response.content}")

        if response.status_code == 202:
            flash('Email sent successfully.', 'success')
            return True
        else:
            error_message = f"Failed to send email: {response.status_code} - {response.content.decode()}"
            flash(error_message, 'error')
            logging.error(error_message)
            return False

    except requests.exceptions.RequestException as e:
        error_content = response.content.decode() if response else 'No response content'
        error_message = f"Failed to send email via Graph API: {e}. Response content: {error_content}"
        flash(error_message, 'error')
        logging.error(error_message)
        return False

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

def generate_reset_token(user):
    # Function that handles reset token generation and setting expiration
    if not user:
        raise ValueError("User must be provided")

    user.reset_token = secrets.token_urlsafe(64)
    user.reset_token_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    db.session.commit()

@app.route('/send_password_reset', methods=['POST'])
def send_password_reset():
    email = request.form.get('email')
    
    # Fetch the user based on the provided email
    user = User.query.filter_by(email=email).first()

    if user:
        # Call the function to generate reset token and set expiration
        generate_reset_token(user)  # This function sets the reset_token and expiration
        
        # Construct the reset link
        reset_link = url_for('reset_password', token=user.reset_token, _external=True)

        # Send the password reset email
        subject = "Password Reset Request"
        body = f"""
        Dear {user.first_name},

        You have requested to reset your password. Please click the link below to reset your password:

        {reset_link}

        If you did not request this, please ignore this email.

        Best regards,
        Your Team
        """
        send_user_email(user.email, subject, body)

        return jsonify({'status': 'success', 'message': 'Password reset link sent.'})
    else:
        return jsonify({'status': 'error', 'message': 'User not found.'})

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if user and user.reset_token_expiration > datetime.utcnow():
        if request.method == 'POST':
            new_password = request.form.get('new_password')
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiration = None
            db.session.commit()
            flash('Your password has been reset. Please log in.', 'success')
            return redirect(url_for('login'))
        # Pass the token to the template
        return render_template('reset_password.html', token=token)
    else:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))


# Route for the dashboard (home page)
@app.route('/')
@login_required
def dashboard():
    user = current_user
    if not user.reset_token or user.reset_token_expiration < datetime.utcnow():
        # Generate a new reset token
        user.reset_token = secrets.token_urlsafe(64)
        user.reset_token_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()
    
    email_settings = EmailSettings.query.first()  # Assuming this is part of your current logic
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
    mail_server = request.form.get('mail_server', settings.mail_server)
    mail_port = request.form.get('mail_port', settings.mail_port)
    email_username = request.form.get('email_username', settings.email_username)
    email_password = request.form.get('email_password', settings.email_password)
    use_tls = request.form.get('use_tls', 'false').lower() == 'true'
    use_ssl = request.form.get('use_ssl', 'false').lower() == 'true'
    default_sender_name = request.form.get('default_sender_name', settings.default_sender_name)
    default_sender_email = request.form.get('default_sender_email', settings.default_sender_email)

    # Validate email settings
    if not mail_server:
        return jsonify({'status': 'error', 'message': 'Mail server is required.'}), 400
    if not email_username or not email_password:
        return jsonify({'status': 'error', 'message': 'Email username and password are required.'}), 400
    if not isinstance(mail_port, int) or not (1 <= mail_port <= 65535):
        return jsonify({'status': 'error', 'message': 'Invalid mail port.'}), 400

    settings.mail_server = mail_server
    settings.mail_port = mail_port
    settings.email_username = email_username
    settings.email_password = email_password
    settings.use_tls = use_tls
    settings.use_ssl = use_ssl
    settings.default_sender_name = default_sender_name
    settings.default_sender_email = default_sender_email

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
        elif field == 'oauth_client_id':
            settings.oauth_client_id = value
        elif field == 'oauth_tenant_id':
            settings.oauth_tenant_id = value
        elif field == 'oauth_client_secret':
            settings.oauth_client_secret = value
        else:
            return jsonify({'status': 'error', 'message': 'Invalid field.'}), 400

        db.session.commit()
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
        return jsonify({'status': 'success', 'settings': email_info}), 200
    except Exception as e:
        # Log error for debugging
        print(f"Failed to send test email: {e}")
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
    # Ensure all users are fetched, not filtered by access level
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

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
        return jsonify({'error': 'You do not have permission to perform this action.'}), 403

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
