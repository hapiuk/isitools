from flask import Flask, render_template, request, send_from_directory, jsonify, flash, redirect, send_file, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import shutil
import zipfile
import sqlite3
import random


# Import configurations and pdf processing functions
from modules.config import Config
from modules.pdf_processing.pdf_utils import process_puwer_documents, process_loler_pdfs, allowed_file, clear_input_folder

app = Flask(__name__)
app.config.from_object(Config)

# Database helper functions
def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/aecom', methods=['GET', 'POST'])
def aecom():
    if request.method == 'POST':
        # Clear the input folder
        clear_input_folder(app.config['UPLOAD_FOLDER'])

        # Process file uploads
        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print(f"{filename} uploaded successfully.")
            else:
                print("Invalid file type.")

        # Process the uploaded files
        business_entity = request.form.get('business_entity', '')
        try:
            process_puwer_documents(app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'],
                                    app.config['PROCESSED_FOLDER'], business_entity, get_db)

            # Prepare files for download
            files_to_zip = []
            for root, _, files in os.walk(app.config['OUTPUT_FOLDER']):
                for file in files:
                    if file.startswith(f"{business_entity}-PWR-") or file.startswith(f"{business_entity}-FAULTYREPORTS-"):
                        files_to_zip.append(os.path.join(root, file))

            if not files_to_zip:
                print("No files found for the specified business entity.")
                return redirect(request.url)

            temp_folder = os.path.join(app.config['TEMP_DOWNLOAD_FOLDER'], business_entity)
            os.makedirs(temp_folder, exist_ok=True)

            for file_to_zip in files_to_zip:
                shutil.move(file_to_zip, os.path.join(temp_folder, os.path.basename(file_to_zip)))

            zip_filename = f"{business_entity}_output.zip"
            zip_path = os.path.join(app.config['TEMP_DOWNLOAD_FOLDER'], zip_filename)
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for file in os.listdir(temp_folder):
                    zip_file.write(os.path.join(temp_folder, file), file)

            shutil.rmtree(temp_folder)
            print("Files processed and zipped successfully.")
            return send_from_directory(app.config['TEMP_DOWNLOAD_FOLDER'], zip_filename, as_attachment=True)

        except Exception as e:
            print(f"Error processing files: {str(e)}")
            return redirect(request.url)

    # Fetch data from aecom_reports table
    conn = get_db()

    # Create the table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aecom_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_ref TEXT,
            inspection_date TEXT,
            document_name TEXT,
            business_entity TEXT
        )
    ''')

    aecom_reports = conn.execute('SELECT * FROM aecom_reports ORDER BY id').fetchall()
    conn.close()

    # Render the template with the fetched data
    return render_template('aecom.html', aecom_reports=aecom_reports)


@app.route('/loler-reports', methods=['GET', 'POST'])
def loler_reports():
    if request.method == 'POST':
        clear_input_folder(app.config['UPLOAD_FOLDER'])

        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print(f"{filename} uploaded successfully.")
            else:
                print("Invalid file type.")

        client_name = request.form.get('client_name')
        if not client_name:
            print("Client name is required.")
            return redirect(request.url)

        # Pass get_db as an argument to process_loler_pdfs
        csv_file_path = process_loler_pdfs(app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], client_name, get_db)
        print(f"CSV File Path: {csv_file_path}")
        if csv_file_path:
            return send_file(csv_file_path, as_attachment=True)
        else:
            print("Error occurred in processing files.")
            return redirect(request.url)

    # Fetch the LOLER inspections from the database
    conn = get_db()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS loler_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            report_date TEXT,
            next_inspection_date TEXT,
            report_count INTEGER
        )
    ''')
    
    loler_inspections = conn.execute('SELECT * FROM loler_inspections').fetchall()
    conn.close()

    return render_template('loler-reports.html', loler_inspections=loler_inspections)


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

@app.route('/add-asset', methods=['POST'])
def add_asset():
    device_type = request.form.get('deviceType')
    make_model = request.form.get('makeModel')
    serial_number = request.form.get('serialNumber')
    imei = request.form.get('imei')
    mac_address = request.form.get('macAddress')
    allocated_user = request.form.get('allocatedUser')

    # Generate a unique ISI number and current timestamp
    isi_number = f"ISI-{random.randint(1000, 9999)}-{int(datetime.now().timestamp())}"
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO assets (isi_number, device_type, make_model, serial_number, imei, mac_address, allocated_user, date_stamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (isi_number, device_type, make_model, serial_number, imei, mac_address, allocated_user, current_timestamp))
        conn.commit()
        success_message = "Asset successfully added."
        error_message = ""  # No error occurred
    except Exception as e:
        success_message = ""
        error_message = f"Error adding asset: {e}"  # Set error message
    finally:
        conn.close()

    return redirect(url_for('assettracker', success=success_message, error=error_message))

@app.route('/delete-asset', methods=['POST'])
def delete_asset():
    isi_number = request.form.get('isi_number')
    conn = get_db()
    try:
        conn.execute('DELETE FROM assets WHERE isi_number = ?', (isi_number,))
        conn.commit()
        success_message = "Asset successfully deleted."
        error_message = ""
    except Exception as e:
        success_message = ""
        error_message = f"Error deleting asset: {e}"
    finally:
        conn.close()
    return redirect(url_for('assettracker', success=success_message, error=error_message))


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
        ip_port = input("Enter the IP address port to run the app (e.g., 5000): ")
        if is_valid_ip(ip_address):
            break
        else:
            print("Invalid IP address. Please enter a valid IP address.")

    print(f"Running the app at IP address: {ip_address}")
    print(f"on port: {ip_port}")

    app.secret_key = 'Is1S3cr3tk3y'
    app.run(host=ip_address, port=ip_port, debug=True)
