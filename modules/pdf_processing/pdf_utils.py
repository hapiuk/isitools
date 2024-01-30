import os
import re
import pdfplumber
import csv
import datetime
from PyPDF2 import PdfMerger

# Functions from pdfextract.py
def merge_pdfs(pdf_files, output_path):
    merger = PdfMerger()
    for pdf in pdf_files:
        with open(pdf, "rb") as pdf_file:
            merger.append(pdf_file)
    with open(output_path, "wb") as merged_pdf:
        merger.write(merged_pdf)

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text(x_tolerance=2)
    return text

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def clear_input_folder(upload_folder):
    pdf_files = [file for file in os.listdir(upload_folder) if file.endswith('.pdf')]
    for pdf_file in pdf_files:
        file_path = os.path.join(upload_folder, pdf_file)
        os.remove(file_path)
        print(f"Deleted: {file_path}")

def extract_information(text, business_entity):
    inspection_no = re.search(r"#InspectionID#\s*(\d+)", text)
    job_no = re.search(r"#JobID#\s*(\d+)", text)
    client_id = re.search(r"#ClientID#\s*(.+)", text)
    serial_no = re.search(r"#SerialNumber#\s*(.+)", text)
    date = re.search(r"#VisitDate#\s*(\d{2}/\d{2}/\d{4})", text)

    intolerable = re.search(r"Intolerable - Defects requiring immediate action\s*(.+)", text)
    substantial = re.search(r"Substantial - Defects requiring attention within a(?:\stime period)?\s*(.+)", text)
    moderate = re.search(r"Moderate - Other defects requiring attention\s*(.+)", text)

    priority = ""
    if intolerable and intolerable.group(1).strip().lower() not in ["", "none"]:
        priority = "Intolerable"
    elif substantial and substantial.group(1).strip().lower() not in ["", "none"]:
        priority = "Substantial"
    elif moderate and moderate.group(1).strip().lower() not in ["", "none"]:
        priority = "Moderate"

    remedial_works = []
    if intolerable and intolerable.group(1).strip().lower() != "none":
        remedial_works.append(intolerable.group(1).strip())
    if substantial and substantial.group(1).strip().lower() != "none":
        remedial_works.append(substantial.group(1).strip())
    if moderate and moderate.group(1).strip().lower() != "none":
        remedial_works.append(moderate.group(1).strip())

    remedial_works_notes = " ".join(remedial_works)

    if date:
        date_action_raised = datetime.datetime.strptime(date.group(1), "%d/%m/%Y")
        formatted_date = date_action_raised.strftime("%d%m%Y")

        if priority == "Moderate":
            target_date = date_action_raised + datetime.timedelta(days=180)
        elif priority == "Substantial":
            target_date = date_action_raised + datetime.timedelta(days=30)
        elif priority == "Intolerable":
            target_date = date_action_raised + datetime.timedelta(days=7)
        else:
            target_date = None

        if target_date:
            target_completion_date = target_date.strftime("%d/%m/%Y")
        else:
            target_completion_date = ""
    else:
        target_completion_date = ""

    info = {
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
        "Property Inspection Ref No": "",
        "Compliance or Asset Type_External Ref No": f"{business_entity}PWR",
        "Property_Business Entity": business_entity,
    }

    return info

def extract_additional_information(text, business_entity, date_str):
    job_no = re.search(r"#JobID#\s*(\d+)", text)

    date_obj = datetime.datetime.strptime(date_str, "%d%m%Y")

    additional_info = {
        "Compliance or Asset Ref No": f"{business_entity}PWR",
        "External Inspection Ref No": f"{business_entity}-PWR-{date_str}-{job_no.group(1) if job_no else ''}",
        "Inspection Date": f"{date_obj.strftime('%d/%m/%Y')}",
        "Contractor": "ISI",
        "Document": f"{business_entity}.-PWR-{date_str}.pdf",
        "Remedial Works": "Yes",
        "Risk Rating": "",
        "Comments": "",
        "Archive": "",
        "Exclude from KPI": "",
        "Inspection Fully Completed": "Yes",
        "Properties_Business Entity": f"{business_entity}",
    }

    # New code to add the second row with headers
    additional_info_secondary = {
        "Compliance or Asset Ref No": "Asset No",
        "External Inspection Ref No": "Inspection Ref / Job No",
        "Inspection Date": "Inspection Date",
        "Contractor": "Contractor",
        "Document": "Document",
        "Remedial Works": "Remedial Works",
        "Risk Rating": "Risk Rating",
        "Comments": "Comments",
        "Archive": "Archive?",
        "Exclude from KPI": "Exclude from KPI",
        "Inspection Fully Completed": "Inspection Fully Completed?",
        "Properties_Business Entity": "Business Entity",
    }

    return additional_info, additional_info_secondary

def process_puwer_documents(input_folder, output_folder, processed_folder, business_entity, get_db):
    processed_pdfs = []
    faulty_reports_pdfs = []
    first_report_date = None
    additional_info_for_db = None

    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            text = extract_text_from_pdf(pdf_path)

            if "#JobType# PUWER" in text or "#JobType# SkippedInspection" in text:
                information = extract_information(text, business_entity)

                if information["Remedial Works Action Required Notes"].strip().lower() == "none":
                    faulty_reports_pdfs.append(pdf_path)
                    continue

                if first_report_date is None:
                    date_match = re.search(r"#VisitDate#\s*(\d{2}/\d{2}/\d{4})", text)
                    if date_match:
                        first_report_date = datetime.datetime.strptime(date_match.group(1), "%d/%m/%Y")

                if additional_info_for_db is None:
                    additional_info_for_db = extract_additional_information(text, business_entity, first_report_date.strftime('%d%m%Y'))

                processed_pdfs.append(pdf_path)
            else:
                faulty_reports_pdfs.append(pdf_path)  # Move faulty reports PDF


    main_merged_pdf_path = os.path.join(output_folder, f"{business_entity}-PWR-{first_report_date.strftime('%d%m%Y')}.pdf")
    faulty_reports_path = os.path.join(output_folder, f"{business_entity}-FAULTYREPORTS-{first_report_date.strftime('%d%m%Y')}.pdf")

    merge_pdfs(processed_pdfs, main_merged_pdf_path)

    if faulty_reports_pdfs:
        merge_pdfs(faulty_reports_pdfs, faulty_reports_path)

    date_str = first_report_date.strftime('%d%m%Y')

    csv_file = os.path.join(output_folder, f"{business_entity}-PWR-{date_str}-REMEDIALACTIONS.csv")
    csv_additional_file = os.path.join(output_folder, f"{business_entity}-PWR-{date_str}.csv")

    header = ["Inspection Ref No", "Remedial Reference Number", "Action Owner", "Date Action Raised", "Corrective Job Number", "Remedial Works Action Required Notes", "Priority", "Target Completion Date", "Actual Completion Date", "PiC Comments", "Property Inspection Ref No", "Compliance or Asset Type_External Ref No", "Property_Business Entity"]

    # Define the secondary header for the main CSV file
    secondary_header_main = [
        "Inspection Ref / Job No",
        "Remedial Reference Number",
        "Action Owner",
        "Date Action Raised",
        "Corrective Job Number",
        "Remedial Works Action Required/Notes",
        "Priority",
        "Target Completion Date",
        "Actual Completion Date",
        "PiC Comments",
        "Property Inspection Ref. No.",
        "Asset No",
        "Business Entity",
    ]

    # Define the secondary header for the additional CSV file
    secondary_header_additional = [
        "Compliance or Asset Ref No",
        "External Inspection Ref No",
        "Inspection Date",
        "Contractor",
        "Document",
        "Remedial Works",
        "Risk Rating",
        "Comments",
        "Archive",
        "Exclude from KPI",
        "Inspection Fully Completed",
        "Properties_Business Entity",
    ]

    with open(csv_file, "w", newline='', encoding='utf-8') as csvfile, open(csv_additional_file, "w", newline='', encoding='utf-8') as csv_additionalfile:
        csvwriter = csv.writer(csvfile)
        csv_additional_writer = csv.writer(csv_additionalfile)

        # Write the first row of headers for both CSV files
        csvwriter.writerow(header)
        
        # Write the secondary header for the main CSV file
        csvwriter.writerow(secondary_header_main)
        
        # Write the secondary header for the additional CSV file
        csv_additional_writer.writerow(secondary_header_additional)

        # Extract job_no from the Inspection Ref / Job No
        job_no = information["Inspection Ref No"].split("-")[-1]
        
        # Write the second row with additional information for both CSV files
        additional_info, additional_info_secondary = extract_additional_information(text, business_entity, date_str)
        csv_additional_writer.writerow(additional_info_secondary.values())

        csv_additional_writer.writerow(additional_info.values())

        for pdf_path in processed_pdfs:
            text = extract_text_from_pdf(pdf_path)
            information = extract_information(text, business_entity)
            if information["Priority"] in ["Intolerable", "Substantial", "Moderate"]:
                row = [information[key] for key in header]
                csvwriter.writerow(row)
                
        if additional_info_for_db is not None:
            # Pass only the first dictionary of the tuple to db_insert_function
            db_insert_function(additional_info_for_db[0], get_db)

    return main_merged_pdf_path, faulty_reports_path, csv_file, csv_additional_file, first_report_date, date_str

def db_insert_function(additional_info, get_db):
    # Extract needed information
    inspection_ref = additional_info["External Inspection Ref No"]
    inspection_date = additional_info["Inspection Date"]
    document_name = additional_info["Document"]
    business_entity = additional_info["Properties_Business Entity"]

    # Database interaction
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

    # Insert data into the table
    conn.execute('''
        INSERT INTO aecom_reports (inspection_ref, inspection_date, document_name, business_entity) 
        VALUES (?, ?, ?, ?)
    ''', (inspection_ref, inspection_date, document_name, business_entity))
    
    conn.commit()
    conn.close()


def process_loler_pdfs(input_folder, output_folder, client_name, get_db):
    # Create the output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Variables to track report dates and count
    earliest_next_inspection_date = "N/A"
    report_date = None
    report_count = 0

    # Generate a unique filename based on client_name
    unique_filename = generate_unique_filename(client_name)
    csv_output_file = os.path.join(output_folder, unique_filename)

    with open(csv_output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write headers to the CSV
        csvwriter.writerow(['Client Name', 'Equipment Type', 'ISI Number', 'Serial Number', 'DOM', 'SWL',
                            'Client Ref', 'Location', 'Report ID', 'A Defect', 'B Defect', 'C Defect', 'D Defect',
                            'Report Date', 'Next Inspection Date'])

        for filename in os.listdir(input_folder):
            if filename.endswith(".pdf"):
                report_count += 1
                pdf_path = os.path.join(input_folder, filename)
                text = extract_text_from_pdf(pdf_path)

                # Extract information between "### Metadata ###" and "### End Metadata ###"
                metadata_match = re.search(r"### Metadata ###(.*?)### End Metadata ###", text, re.DOTALL)
                if metadata_match:
                    metadata_section = metadata_match.group(1).strip()

                    # Extract relevant information from the metadata section
                    metadata_dict = {}

                    # Define the keys to extract
                    keys_to_extract = ['Equipment Type', 'ISI Number', 'Serial Number', 'DOM', 'SWL',
                                       'Client Ref', 'Location', 'Report ID', 'A Defect', 'B Defect', 'C Defect', 'D Defect']

                    for key in keys_to_extract:
                        key_match = re.search(rf"{key}\s*([^\n]*)", metadata_section)
                        metadata_dict[key] = key_match.group(1).strip() if key_match else ""

                    # Extract report date and next inspection date
                    date_match = re.search(r"Report Date\s*([^\n]*)", text)
                    report_date = date_match.group(1).strip() if date_match else ""

                    date_match = re.search(r"Next Inspection Date\s*([^\n]*)", text)
                    next_inspection_date = date_match.group(1).strip() if date_match else ""

                    # Write the row to CSV
                    csvwriter.writerow([client_name] + [metadata_dict.get(key, "") for key in keys_to_extract] + [report_date, next_inspection_date])

                    print(f"CSV Row written for {filename}")

                    if report_date is None:
                        report_date = datetime.strptime(metadata_dict['Report Date'], '%d/%m/%Y')
                    if 'Next Inspection Date' in metadata_dict:
                        next_date = datetime.strptime(metadata_dict['Next Inspection Date'], '%d/%m/%Y')
                        if earliest_next_inspection_date is None or next_date < earliest_next_inspection_date:
                            earliest_next_inspection_date = next_date

    # Insert data into the database
    db_insert_loler_inspection(client_name, report_date, earliest_next_inspection_date, report_count, get_db)

    return csv_output_file

 
def db_insert_loler_inspection(client_name, report_date, next_inspection_date, report_count, get_db):
    # Database interaction
    try:
        conn = get_db()
        # Create the table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS loler_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                report_date TEXT,
                next_inspection_date TEXT,
                report_count INTEGER
            )
        ''')

        # Insert data into the table
        conn.execute('''
            INSERT INTO loler_inspections (client_name, report_date, next_inspection_date, report_count) 
            VALUES (?, ?, ?, ?)
        ''', (client_name, report_date, next_inspection_date, report_count))
        
        conn.commit()
    except Exception as e:
        print(f"Database operation error: {e}")
    finally:
        conn.close()



def db_insert_loler_inspection(client_name, report_date, next_inspection_date, report_count, get_db):
    try:
        conn = get_db()
        # Create the table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS loler_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                report_date TEXT,
                next_inspection_date TEXT,
                report_count INTEGER
            )
        ''')

        # Convert report_date and next_inspection_date to strings if they are datetime objects
        report_date_str = report_date.strftime('%Y-%m-%d') if isinstance(report_date, datetime.datetime) else report_date
        next_inspection_date_str = next_inspection_date.strftime('%Y-%m-%d') if isinstance(next_inspection_date, datetime.datetime) else next_inspection_date

        # Insert data into the table
        conn.execute('''
            INSERT INTO loler_inspections (client_name, report_date, next_inspection_date, report_count) 
            VALUES (?, ?, ?, ?)
        ''', (client_name, report_date_str, next_inspection_date_str, report_count))
        
        conn.commit()
    except Exception as e:
        print(f"Database operation error: {e}")
    finally:
        conn.close()


# Generate a unique filename (from lolerextract.py)
def generate_unique_filename(client_name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H")
    filename = f"{client_name}_{timestamp}.csv"
    return filename