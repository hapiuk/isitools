# aecom.py - AECOM Blueprint
from flask import Blueprint, request, redirect, url_for, flash, jsonify, app
from flask_login import login_required
import os
import pandas as pd
from werkzeug.utils import secure_filename

aecom_blueprint = Blueprint('aecom', __name__)

UPLOAD_FOLDER = 'static/uploads'  # Define where to save uploaded files
ALLOWED_EXTENSIONS = {'csv'}

def extract_information(text, business_entity):
    # Existing extraction logic
    # Continue existing extraction as you provided

    info = {
        # Map fields as needed
        "Inspection Ref No": f"{business_entity}-PWR-{formatted_date}-{job_no.group(1) if job_no else ''}",
        "Remedial Reference Number": f"{business_entity}-PWR-{formatted_date}-{job_no.group(1) if job_no else ''}-{inspection_no.group(1) if inspection_no else ''}",
        "Action Owner": "NSC",
        "Date Action Raised": date.group(1) if date else "",
        "Corrective Job Number": "",
        "Remedial Works Action Required Notes": f"{remedial_works_notes} - Client-ID:{client_id.group(1)}, - Serial Number:{serial_no.group(1)}",
        "Priority": priority,
        "Target Completion Date": target_completion_date,
        "Actual Completion Date": "",
        "PiC Comments": "",
        "Supplementary Notes": "",
        "Property Inspection Ref No": "",
        "Send Email": False,
        "Compliance or Asset Type_External Ref No": f"{business_entity}PWR",
        "Properties_Business Entity": business_entity,
        "Site name": ""  # Set appropriately
    }

    # Insert into Visits Table
    with current_app.app_context():
        db = current_app.extensions['sqlalchemy'].db
        visit = Visit(
            compliance_or_asset_ref_no=info['Compliance or Asset Type_External Ref No'],
            external_inspection_ref_no=info['Inspection Ref No'],
            inspection_date=datetime.strptime(info['Date Action Raised'], '%d/%m/%Y') if info['Date Action Raised'] else None,
            contractor='ISI',  # Default or from extraction
            document=f"{business_entity}-PWR-{formatted_date}.pdf",
            remedial_works='Yes' if info['Remedial Works Action Required Notes'] else 'No',
            properties_business_entity=info['Properties_Business Entity'],
            site_name=info['Site name']
        )
        db.session.add(visit)
        db.session.commit()  # Save visit to get visit_id

        # Insert into Inspections Table
        inspection = Inspection(
            visit_id=visit.id,
            inspection_ref_no=info['Inspection Ref No'],
            remedial_reference_number=info['Remedial Reference Number'],
            action_owner=info['Action Owner'],
            date_action_raised=datetime.strptime(info['Date Action Raised'], '%d/%m/%Y') if info['Date Action Raised'] else None,
            corrective_job_number=info['Corrective Job Number'],
            remedial_works_action_required_notes=info['Remedial Works Action Required Notes'],
            priority=info['Priority'],
            target_completion_date=datetime.strptime(info['Target Completion Date'], '%d/%m/%Y') if info['Target Completion Date'] else None,
            pic_comments=info['PiC Comments'],
            supplementary_notes=info['Supplementary Notes'],
            property_inspection_ref_no=info['Property Inspection Ref No'],
            send_email=info['Send Email'],
            compliance_or_asset_type_external_ref_no=info['Compliance or Asset Type_External Ref No'],
            properties_business_entity=info['Properties_Business Entity'],
            site_name=info['Site name']
        )
        db.session.add(inspection)
        db.session.commit()  # Save inspection

    return info

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@aecom_blueprint.route('/process_aecom_reports', methods=['POST'])
@login_required
def process_aecom_reports():
    business_entity = request.form['business_entity']
    report_files = request.files.getlist('report_files')

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    try:
        for file in report_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                # Example processing logic: read CSV and do something with it
                df = pd.read_csv(filepath)
                # Use db within the current app context
                with current_app.app_context():
                    db = current_app.extensions['sqlalchemy'].db
                    # Example: perform database operations here
                    # db.session.add(...)
                    # db.session.commit()

        flash('AECOM reports processed successfully.', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error processing AECOM reports: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@aecom_blueprint.route('/historic_aecom_reports', methods=['GET'])
@login_required
def historic_aecom_reports():
    reports = []  # Replace with actual database query to get reports
    return jsonify(reports)
