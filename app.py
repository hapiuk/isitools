import os, smtplib, random, string, requests, base64, logging, secrets, re, csv, zipfile
from datetime import date, datetime, timedelta, timezone
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text 
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PyPDF2 import PdfReader

logging.basicConfig(level=logging.DEBUG)

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'isitools26092024'  # Replace with your actual secret key


# Configure the SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'static', 'db', 'isitools.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['MERGED_FOLDER'] = os.path.join(BASE_DIR, 'static', 'merged')
app.config['PROCESSED_FOLDER'] = os.path.join(BASE_DIR, 'static', 'processed')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MERGED_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)  # Initialize Flask-Mail
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Initialize the LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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

class Visit(db.Model):
    __tablename__ = 'visits'
    id = db.Column(db.Integer, primary_key=True)
    compliance_or_asset_ref_no = db.Column(db.String, nullable=False)
    external_inspection_ref_no = db.Column(db.String, nullable=False)
    inspection_date = db.Column(db.Date, nullable=False)
    contractor = db.Column(db.String, default='ISI')
    document = db.Column(db.String)
    remedial_works = db.Column(db.String)
    risk_rating = db.Column(db.String)
    comments = db.Column(db.String)
    archive = db.Column(db.Boolean, default=False)
    exclude_from_kpi = db.Column(db.Boolean, default=False)
    inspection_fully_completed = db.Column(db.Boolean, default=True)
    properties_business_entity = db.Column(db.String)
    site_name = db.Column(db.String)
    link = db.Column(db.String)  # New column for the download link
    inspections = db.relationship('Inspection', backref='visit', lazy=True)  # Establish relationship

class Inspection(db.Model):
    __tablename__ = 'inspections'
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)  # Link to Visit table
    inspection_ref_no = db.Column(db.String, nullable=False)
    remedial_reference_number = db.Column(db.String)
    action_owner = db.Column(db.String, default='NSC')
    date_action_raised = db.Column(db.Date)
    corrective_job_number = db.Column(db.String)
    remedial_works_action_required_notes = db.Column(db.String)
    priority = db.Column(db.String)
    target_completion_date = db.Column(db.Date)
    actual_completion_date = db.Column(db.Date, nullable=True)
    pic_comments = db.Column(db.String)
    supplementary_notes = db.Column(db.String)
    property_inspection_ref_no = db.Column(db.String)
    send_email = db.Column(db.Boolean, default=False)
    compliance_or_asset_type_external_ref_no = db.Column(db.String)
    properties_business_entity = db.Column(db.String)
    site_name = db.Column(db.String)

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

def send_user_email(to_address, subject, html_content):
    settings = EmailSettings.query.first()

    if not settings:
        flash("Email settings are not configured properly in the database.", "error")
        return False

    try:
        token = get_oauth_token()
        if not token:
            return False

        # Set up the Graph API endpoint for sending mail
        sender_email = settings.default_sender_email
        graph_api_url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"

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

        if response.status_code == 202:
            flash('Email sent successfully.', 'success')
            return True
        else:
            error_message = f"Failed to send email: {response.status_code} - {response.content.decode()}"
            flash(error_message, 'error')
            logging.error(error_message)
            return False

    except requests.exceptions.RequestException as e:
        error_message = f"Failed to send email via Graph API: {e}. Response content: {response.content.decode()}"
        flash(error_message, 'error')
        logging.error(error_message)
        return False

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()  # This will create the email_settings table if it doesn't exist

def clear_input_folder(folder_path):
    # Ensure the folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # Clear the folder contents
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove file or link
            elif os.path.isdir(file_path):
                os.rmdir(file_path)   # Remove directory
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def allowed_file(filename, allowed_extensions):
    # Check if the file has a valid extension
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def initialize_email_settings():
    if not EmailSettings.query.first():
        default_settings = EmailSettings(
            mail_server='smtp.example.com',
            mail_port=587,
            email_username='user@example.com',
            email_password='securepassword',
            use_tls=True,
            use_ssl=False,
            default_sender_name='Default Name',
            default_sender_email='default@example.com'
        )
        db.session.add(default_settings)
        db.session.commit()

with app.app_context():
    initialize_email_settings()

# AECOM CODE #########################################
# AECOM CODE #########################################
# AECOM CODE #########################################

def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def process_date(date_value):
    # Converts a datetime object to a date object; if None, return as is
    if isinstance(date_value, datetime):
        return date_value.date()
    return date_value

def get_highest_severity(inspection_entries):
    severity_levels = {
        'Intolerable': 1,
        'Substantial': 2,
        'Moderate': 3,
        'Tolerable': 4,
        'Clear': 5,
        'Asset Not Inspected': 6
    }

    min_severity = float('inf')
    for entry in inspection_entries:
        priority = entry.get('priority', 'Clear')
        severity = severity_levels.get(priority, 5)  # Default to 'Clear' if priority not found
        if severity < min_severity:
            min_severity = severity
    return min_severity

def merge_pdfs(upload_folder, processed_folder, pdf_files, output_filename, cover_pdf=None):
    from PyPDF2 import PdfMerger

    merger = PdfMerger()

    # Add the cover PDF first if it exists
    if cover_pdf and os.path.exists(cover_pdf):
        print(f"Adding cover PDF to merger: {cover_pdf}")
        merger.append(cover_pdf)

    # Sort the PDFs by severity (lower number means higher severity)
    pdf_files_sorted = sorted(pdf_files, key=lambda x: x[1])

    # Append the rest of the PDFs
    for pdf_path, severity in pdf_files_sorted:
        print(f"Adding inspection PDF to merger: {pdf_path} with severity {severity}")
        merger.append(pdf_path)

    # Ensure the processed folder exists
    os.makedirs(processed_folder, exist_ok=True)

    # Save the merged PDF
    output_path = os.path.join(processed_folder, output_filename)
    with open(output_path, 'wb') as f_out:
        merger.write(f_out)

    merger.close()
    print(f"Merged PDF saved to: {output_path}")

def extract_information_from_pdf(text, business_entity):
    # Detect if the document is a Notice of Non-Examination
    is_non_examination = 'Notice of Non-Examination' in text

    # Extract key identifiers
    inspection_no = re.search(r"#InspectionID#\s*(\d+)", text)
    inspection_id = inspection_no.group(1) if inspection_no else ''
    job_no = re.search(r"#JobID#\s*(\d+)", text)
    client_id = re.search(r"#ClientID#\s*(.+)", text)
    serial_no = re.search(r"#SerialNumber#\s*(.+)", text)
    date_match = re.search(r"#VisitDate#\s*(\d{2}/\d{2}/\d{4})", text)
    site_name_match = re.search(r"Site\s*(.+)", text)

    # Parse dates
    if date_match:
        date_action_raised = datetime.strptime(date_match.group(1), "%d/%m/%Y")
        formatted_date = date_action_raised.strftime("%d%m%Y")
    else:
        date_action_raised = None
        formatted_date = ""

    # Extract site name
    if site_name_match:
        site_name = site_name_match.group(1).strip()
    else:
        site_name = "UnknownSite"

    # Generate base info
    inspection_ref_no = f"{business_entity}-PWR-{formatted_date}-{job_no.group(1) if job_no else ''}"
    base_info = {
        "compliance_or_asset_ref_no": f"{business_entity}PWR",
        "external_inspection_ref_no": inspection_ref_no,
        "inspection_date": date_action_raised.date() if date_action_raised else None,
        "contractor": 'ISI',
        "comments": "",  # Leave comments blank for the client
        "site_name": site_name,
        "properties_business_entity": business_entity,
        "actual_completion_date": None  # Initially set to None
    }

    # Initialize inspection_entries list
    inspection_entries = []

    if is_non_examination:
        # Extract the reason for non-inspection
        reason_match = re.search(r"Reason equipment was not inspected\s*(.+?)(?=#+|Engineer|$)", text, re.DOTALL)
        reason = reason_match.group(1).strip() if reason_match else "No reason provided."
        reason = ' '.join(reason.split())  # Remove line breaks and extra spaces

        # Construct remedial_reference_number
        remedial_reference_number = f"{inspection_ref_no}-{inspection_id}"

        # Create the inspection entry
        inspection_entry = {
            "visit_id": None,  # Will be set later after the visit is inserted
            "inspection_ref_no": inspection_ref_no,
            "remedial_reference_number": remedial_reference_number,
            "action_owner": 'NSC',
            "date_action_raised": date_action_raised.date() if date_action_raised else None,
            "corrective_job_number": '',
            "remedial_works_action_required_notes": reason,
            "priority": 'Asset Not Inspected',
            "target_completion_date": None,
            "actual_completion_date": None,
            "pic_comments": '',
            "supplementary_notes": '',
            "property_inspection_ref_no": '',
            "send_email": False,
            "compliance_or_asset_type_external_ref_no": base_info['compliance_or_asset_ref_no'],
            "properties_business_entity": base_info['properties_business_entity'],
            "site_name": base_info['site_name']
        }

        inspection_entries.append(inspection_entry)

    else:
        # Existing logic for standard inspection reports
        # Extract all defects
        defects = []
        defect_patterns = [
            ('Intolerable', r"Intolerable - Defects requiring immediate action\s*(.+?)(?=Substantial|Moderate|Tolerable|#|$)"),
            ('Substantial', r"Substantial - Defects requiring attention within a(?:\s*time period)?\s*(.+?)(?=Intolerable|Moderate|Tolerable|#|$)"),
            ('Moderate', r"Moderate - Other defects requiring attention\s*(.+?)(?=Intolerable|Substantial|Tolerable|#|$)"),
            ('Tolerable', r"Tolerable - Observations\s*(.+?)(?=Intolerable|Substantial|Moderate|#|$)")
        ]

        for priority, pattern in defect_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                defect_description = match.strip()
                if defect_description and defect_description.lower() != 'none':
                    # Remove line breaks from the defect description
                    defect_description = ' '.join(defect_description.split())
                    defects.append({
                        'priority': priority,
                        'description': defect_description
                    })

        # Generate a list of inspection entries
        if defects:
            for defect in defects:
                priority = defect['priority']
                description = defect['description']

                # Append Client ID and Serial Number to remedial works, remove line breaks
                client_info = f"Client-ID: {client_id.group(1).strip() if client_id else 'N/A'}, Serial Number: {serial_no.group(1).strip() if serial_no else 'N/A'}"
                remedial_works = f"{description} {client_info}"

                # Remove any additional line breaks from remedial works
                remedial_works = ' '.join(remedial_works.split())

                # Calculate target completion date based on priority
                if date_action_raised:
                    if priority == "Intolerable":
                        target_date = date_action_raised + timedelta(days=7)
                    elif priority == "Substantial":
                        target_date = date_action_raised + timedelta(days=30)
                    elif priority == "Moderate":
                        target_date = date_action_raised + timedelta(days=180)
                    elif priority == "Tolerable":
                        target_date = date_action_raised + timedelta(days=365)
                    else:
                        target_date = None
                    target_completion_date = target_date.date() if target_date else None
                else:
                    target_completion_date = None

                # Construct remedial_reference_number
                remedial_reference_number = f"{inspection_ref_no}-{inspection_id}"

                # Create the inspection entry
                inspection_entry = {
                    "visit_id": None,  # Will be set later after the visit is inserted
                    "inspection_ref_no": inspection_ref_no,
                    "remedial_reference_number": remedial_reference_number,
                    "action_owner": 'NSC',
                    "date_action_raised": date_action_raised.date() if date_action_raised else None,
                    "corrective_job_number": '',
                    "remedial_works_action_required_notes": remedial_works,
                    "priority": priority,
                    "target_completion_date": target_completion_date,
                    "actual_completion_date": None,
                    "pic_comments": '',
                    "supplementary_notes": '',
                    "property_inspection_ref_no": '',
                    "send_email": False,
                    "compliance_or_asset_type_external_ref_no": base_info['compliance_or_asset_ref_no'],
                    "properties_business_entity": base_info['properties_business_entity'],
                    "site_name": base_info['site_name']
                }

                inspection_entries.append(inspection_entry)
        else:
            # No defects found; create a default inspection entry
            remedial_works = "No defects found."
            remedial_reference_number = f"{inspection_ref_no}-{inspection_id}"
            priority = 'Clear'  # Set default priority to 'Clear'

            # Calculate target completion date (365 days from date_action_raised)
            if date_action_raised:
                target_date = date_action_raised + timedelta(days=365)
                target_completion_date = target_date.date()
            else:
                target_completion_date = None

            inspection_entry = {
                "visit_id": None,  # Will be set later after the visit is inserted
                "inspection_ref_no": inspection_ref_no,
                "remedial_reference_number": remedial_reference_number,
                "action_owner": 'NSC',
                "date_action_raised": date_action_raised.date() if date_action_raised else None,
                "corrective_job_number": '',
                "remedial_works_action_required_notes": remedial_works,
                "priority": priority,
                "target_completion_date": target_completion_date,
                "actual_completion_date": None,
                "pic_comments": '',
                "supplementary_notes": '',
                "property_inspection_ref_no": '',
                "send_email": False,
                "compliance_or_asset_type_external_ref_no": base_info['compliance_or_asset_ref_no'],
                "properties_business_entity": base_info['properties_business_entity'],
                "site_name": base_info['site_name']
            }

            inspection_entries.append(inspection_entry)

    return base_info, inspection_entries

def process_uploaded_pdfs(business_entity):
    upload_folder = app.config['UPLOAD_FOLDER']
    processed_folder = app.config['PROCESSED_FOLDER']

    visit_data = None
    inspections_data = []
    has_remedial_works = False  # Flag to track if high-priority defects exist
    pdf_files = []
    cover_pdf = None

    for filename in os.listdir(upload_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(upload_folder, filename)

            if re.match(r'Job[_ ]\d+\.pdf', filename):
                cover_pdf = pdf_path
                print(f"Cover PDF identified: {filename}")
                continue  # Skip processing the cover PDF as an inspection PDF

            text = extract_text_from_pdf(pdf_path)

            # Extract data from the PDF
            base_info, inspection_entries = extract_information_from_pdf(text, business_entity)

            if not visit_data and base_info:
                visit_data = base_info.copy()

            # Check for high-priority defects
            for entry in inspection_entries:
                if entry['priority'] in ['Moderate', 'Substantial', 'Intolerable']:
                    has_remedial_works = True

            inspections_data.extend(inspection_entries)

            # Determine severity for sorting
            highest_severity = get_highest_severity(inspection_entries)
            pdf_files.append((pdf_path, highest_severity))

    if visit_data:
        visit_data['document'] = visit_data['external_inspection_ref_no'] + '.pdf'
        visit_data['remedial_works'] = 'Yes' if has_remedial_works else 'No'
        visit_data['risk_rating'] = ''
        visit_data['inspection_fully_completed'] = True

        # Insert the visit entry and get the visit_id
        visit_id = insert_visit(visit_data)

        # Now set visit_id in each inspection entry
        for inspection_data in inspections_data:
            inspection_data['visit_id'] = visit_id

        # Insert inspections linked to the visit ID
        insert_inspections(inspections_data)

        # Merge PDFs
        merge_pdfs(upload_folder, processed_folder, pdf_files, visit_data['document'], cover_pdf)

        # Generate the report package now that PDFs are merged and CSVs are generated
        try:
            # Fetch the visit from the database to include in the report package generation
            visit = Visit.query.get(visit_id)
            generate_report_package(visit, inspections_data)
            print("Report package generated successfully.")
        except Exception as e:
            print(f"Error generating report package: {e}")
            flash("Error generating the report package.", "error")

        # Clear the upload folder after processing
        clear_folder(upload_folder)
    else:
        flash("No visit data extracted.", "error")

def insert_visit(extracted_data):
    try:
        # Construct the download link using the 'document' field
        download_link = f"/static/processed/{extracted_data['document']}"

        visit = Visit(
            compliance_or_asset_ref_no=extracted_data['compliance_or_asset_ref_no'],
            external_inspection_ref_no=extracted_data['external_inspection_ref_no'],
            inspection_date=extracted_data['inspection_date'],
            contractor=extracted_data['contractor'],
            document=extracted_data.get('document'),
            remedial_works=extracted_data.get('remedial_works'),
            risk_rating=extracted_data.get('risk_rating'),
            comments=extracted_data.get('comments', ''),
            archive=extracted_data.get('archive', False),
            exclude_from_kpi=extracted_data.get('exclude_from_kpi', False),
            inspection_fully_completed=extracted_data.get('inspection_fully_completed', True),
            properties_business_entity=extracted_data['properties_business_entity'],
            site_name=extracted_data['site_name'],
            link=download_link
        )

        db.session.add(visit)
        db.session.commit()
        return visit.id
    except Exception as e:
        db.session.rollback()
        flash(f"Error inserting visit: {str(e)}", "error")
        return None

def insert_inspections(inspections_data):
    for inspection_data in inspections_data:
        inspection = Inspection(
            visit_id=inspection_data['visit_id'],
            inspection_ref_no=inspection_data['inspection_ref_no'],
            remedial_reference_number=inspection_data['remedial_reference_number'],
            action_owner=inspection_data['action_owner'],
            date_action_raised=inspection_data['date_action_raised'],
            corrective_job_number=inspection_data['corrective_job_number'],
            remedial_works_action_required_notes=inspection_data['remedial_works_action_required_notes'],
            priority=inspection_data['priority'],
            target_completion_date=inspection_data['target_completion_date'],
            actual_completion_date=inspection_data['actual_completion_date'],
            pic_comments=inspection_data['pic_comments'],
            supplementary_notes=inspection_data['supplementary_notes'],
            property_inspection_ref_no=inspection_data['property_inspection_ref_no'],
            send_email=inspection_data['send_email'],
            compliance_or_asset_type_external_ref_no=inspection_data['compliance_or_asset_type_external_ref_no'],
            properties_business_entity=inspection_data['properties_business_entity'],
            site_name=inspection_data['site_name']
        )
        db.session.add(inspection)
    db.session.commit()

def generate_csv_for_visit(visit):
    try:
        # Construct the filename with entity, date, and visit ID
        filename = f"{visit.properties_business_entity}-PWR-{visit.inspection_date.strftime('%d%m%Y')}.csv"
        filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)

        # Primary header (official column names)
        primary_header = [
            "Compliance or Asset Ref No", "External Inspection Ref No", "Inspection Date", "Contractor",
            "Document", "Remedial Works", "Risk Rating", "Comments", "Archive", 
            "Exclude from KPI", "Inspection Fully Completed", "Properties_Business Entity"
        ]

        # Secondary header (alternative column names)
        secondary_header = [
            "Asset No", "Inspection Ref / Job No", "Inspection Date", "Contractor",
            "Document", "Remedial Works", "Risk Rating", "Comments", "Archive?", 
            "Exclude from KPI", "Inspection Fully Completed?", "Business Entity"
        ]

        # Create CSV for visit data
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write the headers
            writer.writerow(primary_header)
            writer.writerow(secondary_header)

            # Extract visit data and convert None values to empty strings
            visit_data = {
                "Compliance or Asset Ref No": visit.compliance_or_asset_ref_no or '',
                "External Inspection Ref No": visit.external_inspection_ref_no or '',
                "Inspection Date": visit.inspection_date.strftime('%d/%m/%Y') if visit.inspection_date else '',
                "Contractor": visit.contractor or '',
                "Document": visit.document or '',
                "Remedial Works": visit.remedial_works or '',
                "Risk Rating": visit.risk_rating or '',
                "Comments": visit.comments or '',
                "Archive": 'Yes' if visit.archive else 'No',
                "Exclude from KPI": 'Yes' if visit.exclude_from_kpi else 'No',
                "Inspection Fully Completed": 'Yes' if visit.inspection_fully_completed else 'No',
                "Properties_Business Entity": visit.properties_business_entity or ''
            }

            # Write the visit data row
            writer.writerow([
                visit_data["Compliance or Asset Ref No"],
                visit_data["External Inspection Ref No"],
                visit_data["Inspection Date"],
                visit_data["Contractor"],
                visit_data["Document"],
                visit_data["Remedial Works"],
                visit_data["Risk Rating"],
                visit_data["Comments"],
                visit_data["Archive"],
                visit_data["Exclude from KPI"],
                visit_data["Inspection Fully Completed"],
                visit_data["Properties_Business Entity"]
            ])

        print(f"CSV generated for visit: {filepath}")
        return filename
    except Exception as e:
        print(f"Unexpected error generating CSV for visit: {e}")
        raise

def generate_csv_for_remedial_actions(visit, inspections):
    try:
        # Construct the filename for remedial actions CSV
        filename = f"{visit.properties_business_entity}-PWR-{visit.inspection_date.strftime('%d%m%Y')}_REMEDIALACTIONS.csv"
        filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)

        if not inspections:
            raise ValueError("No inspections data to generate CSV.")

        # Create CSV for remedial actions
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Define the primary and secondary headers
            primary_header = [
                "Inspection Ref No", "Remedial Reference Number", "Action Owner", "Date Action Raised",
                "Corrective Job Number", "Remedial Works Action Required Notes", "Priority",
                "Target Completion Date", "Actual Completion Date", "PiC Comments", "Supplementary Notes",
                "Property Inspection Ref No", "Send Email", "Compliance or Asset Type_External Ref No",
                "Properties_Business Entity", "Site name"
            ]

            secondary_header = [
                "Inspection Ref / Job No", "Remedial Reference Number", "Action Owner", "Date Action Raised",
                "Corrective Job Number", "Remedial Works Action Required/Notes", "Priority",
                "Target Completion Date", "Actual Completion Date", "PiC Comments", "Supplementary Notes",
                "Property Inspection Ref. No.", "Send Email", "Asset No", "Business Entity", ""
            ]

            # Write the headers
            writer.writerow(primary_header)
            writer.writerow(secondary_header)

            # Write rows for each inspection entry, handling None values and skipping 'send_email'
            for inspection in inspections:
                if inspection.get('priority') in ['Moderate', 'Substantial', 'Intolerable']:  # Only include relevant priorities
                    inspection_data = {
                        "Inspection Ref No": inspection.get('inspection_ref_no', ''),
                        "Remedial Reference Number": inspection.get('remedial_reference_number', ''),
                        "Action Owner": inspection.get('action_owner', ''),
                        "Date Action Raised": inspection.get('date_action_raised', '').strftime('%d/%m/%Y') if inspection.get('date_action_raised') else '',
                        "Corrective Job Number": inspection.get('corrective_job_number', ''),
                        "Remedial Works Action Required Notes": inspection.get('remedial_works_action_required_notes', ''),
                        "Priority": inspection.get('priority', ''),
                        "Target Completion Date": inspection.get('target_completion_date', '').strftime('%d/%m/%Y') if inspection.get('target_completion_date') else '',
                        "Actual Completion Date": inspection.get('actual_completion_date', '').strftime('%d/%m/%Y') if inspection.get('actual_completion_date') else '',
                        "PiC Comments": inspection.get('pic_comments', ''),
                        "Supplementary Notes": inspection.get('supplementary_notes', ''),
                        "Property Inspection Ref No": inspection.get('property_inspection_ref_no', ''),
                        # 'Send Email' intentionally left blank
                        "Compliance or Asset Type_External Ref No": inspection.get('compliance_or_asset_type_external_ref_no', ''),
                        "Properties_Business Entity": inspection.get('properties_business_entity', ''),
                        "Site name": inspection.get('site_name', '')
                    }

                    # Write the inspection data row, ensuring correct order
                    writer.writerow([
                        inspection_data["Inspection Ref No"],
                        inspection_data["Remedial Reference Number"],
                        inspection_data["Action Owner"],
                        inspection_data["Date Action Raised"],
                        inspection_data["Corrective Job Number"],
                        inspection_data["Remedial Works Action Required Notes"],
                        inspection_data["Priority"],
                        inspection_data["Target Completion Date"],
                        inspection_data["Actual Completion Date"],
                        inspection_data["PiC Comments"],
                        inspection_data["Supplementary Notes"],
                        inspection_data["Property Inspection Ref No"],
                        '',  # Send Email column left blank
                        inspection_data["Compliance or Asset Type_External Ref No"],
                        inspection_data["Properties_Business Entity"],
                        inspection_data["Site name"]
                    ])

        print(f"CSV generated for remedial actions: {filepath}")
        return filename
    except Exception as e:
        print(f"Unexpected error generating CSV for remedial actions: {e}")
        raise

def generate_report_package(visit, inspections):
    try:
        # Generate filenames and paths
        pdf_filename = visit.document
        visit_csv = generate_csv_for_visit(visit)
        remedial_actions_csv = generate_csv_for_remedial_actions(visit, inspections)

        processed_folder = os.path.normpath(app.config['PROCESSED_FOLDER'])
        pdf_path = os.path.join(processed_folder, pdf_filename)
        visit_csv_path = os.path.join(processed_folder, visit_csv)
        remedial_csv_path = os.path.join(processed_folder, remedial_actions_csv)

        zip_filename = f"{visit.properties_business_entity}-PWR-{visit.inspection_date.strftime('%d%m%Y')}.zip"
        zip_path = os.path.join(processed_folder, zip_filename)

        # Create a zip file containing the PDF and both CSVs
        try:
            # Zip file creation
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                if os.path.exists(pdf_path):
                    zipf.write(pdf_path, os.path.basename(pdf_path))
                if os.path.exists(visit_csv_path):
                    zipf.write(visit_csv_path, os.path.basename(visit_csv_path))
                if os.path.exists(remedial_csv_path):
                    zipf.write(remedial_csv_path, os.path.basename(remedial_csv_path))
        except Exception as e:
            print(f"Error during zip file creation: {e}")

        # Store the full static path in the link column
        visit.link = f"/static/processed/{zip_filename}"
        db.session.commit()

        print(f"Report package generated at {zip_path}")
        return zip_path
    except Exception as e:
        print(f"Error generating report package: {e}")
        raise

@app.route('/aecom', methods=['GET', 'POST'])
@login_required
def aecom():
    if request.method == 'POST':
        # Clear the upload folder before processing
        clear_folder(app.config['UPLOAD_FOLDER'])

        # Get business_entity from the form data
        business_entity = request.form.get('business_entity', 'DefaultEntity')

        files = request.files.getlist('report_files')
        for file in files:
            if file and allowed_file(file.filename, {'pdf'}):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                print(f"{filename} uploaded successfully.")
            else:
                flash("Invalid file type.", "error")
                return redirect(url_for('dashboard'))

        try:
            # Pass business_entity to process_uploaded_pdfs
            process_uploaded_pdfs(business_entity)
            flash("Files processed and data inserted into the database successfully.", "success")
        except Exception as e:
            error_message = f"Error processing files: {str(e)}"
            print(error_message)
            flash(error_message, "error")

        return redirect(url_for('dashboard'))

    return redirect(url_for('dashboard'))

@app.route('/api/aecom/historic-reports')
@login_required
def api_get_aecom_historic_reports():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    print(f"Fetching AECOM reports: page {page}, per_page {per_page}")
    reports = Visit.query.paginate(page=page, per_page=per_page)  
    print(f"Found {reports.total} reports for AECOM.")

    report_list = [
        {
            'id': report.id,
            'site_name': report.site_name,
            'items_inspected': len(report.inspections),
            'visit_date': report.inspection_date.strftime('%Y-%m-%d'),
            'link': report.link  # Corrected from 'visit.link' to 'report.link'
        } for report in reports.items
    ]

    return jsonify({
        'reports': report_list,
        'total': reports.total,
        'pages': reports.pages,
        'current_page': reports.page
    })

# Route to delete an AECOM historic report
@app.route('/api/aecom/historic-reports/<int:report_id>', methods=['DELETE'])
@login_required
def api_delete_aecom_historic_report(report_id):
    if current_user.access_level != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    # Fetch the report by ID
    report = Visit.query.get(report_id)
    if report and report.properties_business_entity == 'AECOM':
        try:
            db.session.delete(report)
            db.session.commit()
            return jsonify({'success': 'Report deleted'}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to delete report {report_id}: {e}")
            return jsonify({'error': 'Failed to delete report'}), 500
    else:
        return jsonify({'error': 'Report not found'}), 404

### END OF AECOM CODE ########################################
### END OF AECOM CODE ########################################
### END OF AECOM CODE ########################################

@app.route('/process_puwer_reports', methods=['POST'])
@login_required
def process_puwer_reports():
    flash('PUWER Processing has not been added yet.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/process_loler_reports', methods=['POST'])
@login_required
def process_loler_reports():
    flash('LOLER Processing has not been added yet.', 'info')
    return redirect(url_for('dashboard'))

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for the dashboard (home page)
@app.route('/')
@login_required
def dashboard():
    user = current_user
    # Ensure correct datetime usage for token handling
    if not user.reset_token or user.reset_token_expiration < datetime.utcnow():
        # Generate a new reset token
        user.reset_token = secrets.token_urlsafe(64)
        user.reset_token_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()
    
    email_settings = EmailSettings.query.first()
    if not email_settings:
        flash("Email settings are missing or not properly configured.", "error")
        email_settings = {}  # Prevent template errors by using a default empty dict

    # Render the dashboard with required data
    return render_template('dashboard.html', email_settings=email_settings)

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

def generate_secure_random_password():
    # Generates a secure random password
    return secrets.token_urlsafe(16)

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
        generate_reset_token(user)
        
        # Construct the reset link
        reset_link = url_for('reset_password', token=user.reset_token, _external=True)

        # Send the password reset email using the template
        subject = "Password Reset Request"
        html_content = render_template('password_reset_email.html', first_name=user.first_name, reset_link=reset_link)
        send_user_email(user.email, subject, html_content)

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
    password = generate_secure_random_password()

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
    body = f"Hello {first_name},\n\nYour account has been created. Your password is: \n{password}\n\nPlease change it upon your first login."
    try:
        send_user_email(email, subject, body)
        flash('New user created successfully and email sent.', 'success')
    except Exception as e:
        flash(f'User created but failed to send email: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/create_default_user', methods=['GET'])
def create_default_user():
    # Check if the default user already exists
    existing_user = User.query.filter_by(email='it@isisafety.com').first()
    if existing_user:
        flash('Default user already exists.', 'info')
        return redirect(url_for('login'))

    # Generate a secure random password
    random_password = generate_secure_random_password()

    # Create the default admin user with provided details and a secure hashed password
    default_user = User(
        first_name="Default",
        last_name="Admin",
        email="it@isisafety.com",
        department="hell",
        location="underworld",
        access_level="Admin",  # Ensure this matches your access level structure
        password_hash=generate_password_hash(random_password)  # Generate and hash the secure password
    )

    try:
        # Add and commit the user to bind it to the session
        db.session.add(default_user)
        db.session.commit()

        # Re-query the user to ensure it is bound to the session
        default_user = User.query.filter_by(email='it@isisafety.com').first()

        # Generate a reset token and set expiration using your existing function
        generate_reset_token(default_user)

        # Construct the reset link using the token
        reset_link = url_for('reset_password', token=default_user.reset_token, _external=True)

        # Prepare the email content
        subject = "Set Your Admin Account Password"
        body = f"""
        Dear Default Admin,

        Your admin account has been created. Please set your password by clicking the link below:

        {reset_link}

        If you did not request this, please contact support.

        Best regards,
        Your Team
        """
        send_user_email(default_user.email, subject, body)

        flash('Default admin user created. A password reset email has been sent to set the password.', 'success')
    except Exception as e:
        # Rollback in case of any failure
        db.session.rollback()
        flash(f'Failed to create default user or send password reset email: {str(e)}', 'error')

    return redirect(url_for('login'))

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
    return jsonify({'error': '404.'}), 404

# Run the application
if __name__ == "__main__":
    import socket

    def is_valid_ip(ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    ip_address = None
    while True:
        ip_address = input("Enter the IP address to run the app (e.g., 0.0.0.0): ")
        if is_valid_ip(ip_address):
            break
        else:
            print("Invalid IP address. Please enter a valid IP address.")

    print(f"Running the app at IP address: {ip_address}")

    app.secret_key = 'isitools26092024'
    app.run(host=ip_address, port=5000, debug=False)
