import os
import random
import string
import subprocess
import logging
from flask import Flask, request, flash, render_template, redirect, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
import io
import zipfile
import sqlite3
import shutil
from datetime import datetime


UPLOAD_FOLDER = './input'
OUTPUT_FOLDER = './output'
PROCESSED_FOLDER = './processed'
TEMP_DOWNLOAD_FOLDER = './temp_download'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.debug = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'Is1S3cr3tk3y'

logging.basicConfig(level=logging.INFO)

# Database Configuration
DATABASE = './static/isidatabase.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            score INTEGER,
            total_questions INTEGER,
            percentage REAL
        )
    ''')
    conn.commit()
    conn.close()

def create_assets_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isi_number TEXT,
            device_type TEXT,       
            make_model TEXT,      
            serial_number TEXT,
            imei TEXT,
            mac_address TEXT,
            allocated_user TEXT,
            date_stamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_aecomjobs_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aecom_inspections(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Type TEXT,
            inspection_ref TEXT,       
            inspection_date DATE,      
            contractor TEXT,
            document TEXT,
            remedial_works TEXT,
            complete TEXT,
            business_entity TEXT,
            site_name TEXT,
            invoice_group TEXT,
            invoiced TEXT,
            value NUMERIC
        )
    ''')
    conn.commit()
    conn.close()

create_table()
create_assets_table()
create_aecomjobs_table()

@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')

@app.route('/quiz', methods=['GET'])
def quiz():
    return render_template('mockexam.html')

@app.route('/client01')
def client01():
    search_query = request.args.get('search', '', type=str)
    success_message = request.args.get('success', '')
    error_message = request.args.get('error', '')

    conn = get_db()
    
    # Implement filtering based on the search query
    if search_query:
        assets = conn.execute('''
            SELECT * FROM aecom_inspections
            WHERE (Type LIKE ? OR inspection_ref LIKE ? OR inspection_ref LIKE ? OR contractor LIKE ? OR document LIKE ? OR remedial_works LIKE ? OR complete LIKE ? OR business_entity LIKE ? OR site_name LIKE ? OR invoice_group LIKE ? OR invoiced LIKE ? OR value LIKE ?)
            ORDER BY id
            LIMIT ? OFFSET ?
        ''', (f"%{search_query}%",) * 8 + (assets_per_page, (page - 1) * assets_per_page)).fetchall()
    else:
        inspections = conn.execute('''
            SELECT * FROM aecom_inspections
            ORDER BY id
        ''',).fetchall()

    conn.close()
    return render_template('client01.html', inspections=inspections, success_message=success_message, error_message=error_message)

@app.route('/assettracker')
def assettracker():
    search_query = request.args.get('search', '', type=str)
    success_message = request.args.get('success', '')
    error_message = request.args.get('error', '')

    conn = get_db()
    
    # Implement filtering based on the search query
    if search_query:
        assets = conn.execute('''
            SELECT * FROM assets
            WHERE (isi_number LIKE ? OR device_type LIKE ? OR make_model LIKE ? OR serial_number LIKE ? OR imei LIKE ? OR mac_address LIKE ? OR allocated_user LIKE ? OR date_stamp LIKE ?)
            ORDER BY id
            LIMIT ? OFFSET ?
        ''', (f"%{search_query}%",) * 8 + (assets_per_page, (page - 1) * assets_per_page)).fetchall()
    else:
        assets = conn.execute('''
            SELECT * FROM assets
            ORDER BY id
        ''',).fetchall()

    conn.close()
    return render_template('assettracker.html', assets=assets, success_message=success_message, error_message=error_message)

@app.route('/get-asset-details/<isi_number>', methods=['GET'])
def get_asset_details(isi_number):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM assets WHERE isi_number = ?', (isi_number,))
    asset_details = cursor.fetchone()
    conn.close()

    if asset_details:
        asset_details_dict = dict(asset_details)
        app.logger.info(f'Asset details found: {asset_details_dict}')
        return jsonify(asset_details_dict)
    else:
        app.logger.warning('Asset details not found.')
        return jsonify({'error': 'Asset details not found'}), 404

@app.route('/update-asset', methods=['POST'])
def update_asset():
    if request.method == 'POST':
        try:
            # Get data from the form
            isi_number = request.form['isi_number']
            device_type = request.form['device_type']
            make_model = request.form['make_model']
            serial_number = request.form['serial_number']
            imei = request.form['imei']
            mac_address = request.form['mac_address']
            allocated_user = request.form['allocated_user']

            # Update the asset data in the database
            conn = get_db()
            conn.execute('''
                UPDATE assets
                SET device_type=?, make_model=?, serial_number=?, imei=?, mac_address=?, allocated_user=?
                WHERE isi_number=?
            ''', (device_type, make_model, serial_number, imei, mac_address, allocated_user, isi_number))
            conn.commit()
            conn.close()

            success_message = "Asset updated successfully."
            session['success_message'] = success_message
        except Exception as e:
            error_message = str(e)
            session['error_message'] = error_message

    return redirect('/assettracker')


@app.route('/upload')
def page1():
    return render_template('upload.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_input_folder():
    pdf_files = [file for file in os.listdir(UPLOAD_FOLDER) if file.endswith('.pdf')]
    
    for pdf_file in pdf_files:
        file_path = os.path.join(UPLOAD_FOLDER, pdf_file)
        os.remove(file_path)
        print(f"Deleted: {file_path}")

@app.route('/upload', methods=['POST'])
def upload_files():
    clear_input_folder()
    if request.method == 'POST':
        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                flash(f"{filename} uploaded successfully.")
            else:
                flash("Invalid file type.")
    return "Files uploaded."

@app.route('/process', methods=['POST'])
def process_files():
    business_entity = request.args.get('business_entity', '')
    script_path = "./static/pdfextract.py"

    command = [
        "python3",
        script_path,
        "--input",
        UPLOAD_FOLDER,
        "--output",
        OUTPUT_FOLDER,
        "--processed",
        PROCESSED_FOLDER,
        "--business_entity",
        business_entity,
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        output = result.stdout
        date_str = output.strip()
    except subprocess.CalledProcessError as e:
        return f"Error processing files: {str(e)}"

    return "Files processed."

from flask import send_file

@app.route('/download')
def download_files():
    business_entity = request.args.get('business_entity')

    files_to_zip = []
    for root, _, files in os.walk(OUTPUT_FOLDER):
        for file in files:
            if file.startswith(f"{business_entity}-PWR-") or file.startswith(f"{business_entity}-FAULTYREPORTS-") or file.startswith(f"{business_entity}-PWR-"):
                files_to_zip.append(os.path.join(root, file))

    if not files_to_zip:
        return "Files not found for the specified business entity."

    temp_folder = os.path.join(TEMP_DOWNLOAD_FOLDER, business_entity)
    os.makedirs(temp_folder, exist_ok=True)

    csv_additional_file = None
    for file_to_zip in files_to_zip:
        if file_to_zip.endswith("-REMEDIALACTIONS.csv"):
            shutil.move(file_to_zip, os.path.join(temp_folder, os.path.basename(file_to_zip)))
        elif file_to_zip.startswith(f"{business_entity}-PWR-") and file_to_zip.endswith(".csv"):
            csv_additional_file = file_to_zip
            shutil.move(file_to_zip, os.path.join(temp_folder, os.path.basename(file_to_zip)))
        else:
            shutil.move(file_to_zip, os.path.join(temp_folder, os.path.basename(file_to_zip)))

    if csv_additional_file:
        shutil.copy(csv_additional_file, os.path.join(temp_folder, os.path.basename(csv_additional_file)))

    zip_filename = f"{business_entity}_output.zip"
    zip_path = os.path.join(TEMP_DOWNLOAD_FOLDER, zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        for root, _, files in os.walk(temp_folder):
            for file in files:
                zip_file.write(os.path.join(root, file), file)

    shutil.rmtree(temp_folder)

    return send_from_directory(TEMP_DOWNLOAD_FOLDER, zip_filename, as_attachment=True)


@app.route('/save-asset', methods=['POST'])
def save_asset():
    if request.method == 'POST':
        try:
            # Get data from the form
            serial_number = request.form['serial_number']

            # Check if the serial number already exists in the database
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM assets WHERE serial_number = ?', (serial_number,))
            existing_count = cursor.fetchone()[0]
            conn.close()

            if existing_count > 0:
                error_message = "A duplicate serial number cannot be added."
                session['error_message'] = error_message
            else:
                imei = request.form['imei']
                mac_address = request.form['mac_address']
                allocated_user = request.form['allocated_user']
                device_type = request.form['device_type']  # New field
                make_model = request.form['make_model']    # New field
                date_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Get the number of existing assets
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM assets')
                asset_count = cursor.fetchone()[0]

                # Generate the ISI number
                isi_number = 'ISI' + ('00' + str(asset_count + 1))[-3:]

                # Save the asset data to the database
                conn.execute('''
                    INSERT INTO assets (isi_number, serial_number, imei, mac_address, allocated_user, device_type, make_model, date_stamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (isi_number, serial_number, imei, mac_address, allocated_user, device_type, make_model, date_stamp))
                conn.commit()
                conn.close()

                success_message = "Asset added successfully."
                session['success_message'] = success_message

        except Exception as e:
            error_message = "str(e)"
            session['error_message'] = error_message

        return redirect('/assettracker')



@app.route('/leaderboard')
def leaderboard():
    conn = get_db()
    results = conn.execute('SELECT * FROM results ORDER BY percentage DESC').fetchall()
    conn.close()
    return render_template('leaderboard.html', results=results)

def save_results_to_db(name, score, total_questions, percentage):
    conn = get_db()
    conn.execute('INSERT INTO results (name, score, total_questions, percentage) VALUES (?, ?, ?, ?)',
                 (name, score, total_questions, percentage))
    conn.commit()
    conn.close()

@app.route('/save-results', methods=['POST'])
def save_results():
    name = request.json.get('name')
    score = request.json.get('score')
    total_questions = request.json.get('totalQuestions')
    percentage = request.json.get('percentage')

    conn = sqlite3.connect('./static/exam_results.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO results (name, score, total_questions, percentage) VALUES (?, ?, ?, ?)', (name, score, total_questions, percentage))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Results saved successfully'})

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

    app.secret_key = 'topsecret'
    app.run(host=ip_address, port=5000, debug=True)
