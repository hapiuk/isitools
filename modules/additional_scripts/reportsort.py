# This script was created to be used along side the ISI LOLER script (Located in the webapp),
# This can be used without it, but a header with "Location" and "Report ID" must be present
# The script will then sort the reports into thier corresponding folders.

import os
import csv
import shutil

# Path to the directory containing the PDF files
pdf_directory = './'
# Path to the CSV file
csv_file_path = './Merged Reports/GEA Mechanical Equipment UK Limited_20240130-12.csv'
# Path to the directory where the folders will be created
destination_directory = './'

# Read the CSV file
with open(csv_file_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        location = row['Location']
        report_id = row['Report ID']
        file_name = f'Inspection {report_id}.pdf'

        # Check if the file exists
        file_path = os.path.join(pdf_directory, file_name)
        if os.path.isfile(file_path):
            # Create destination folder if it doesn't exist
            folder_path = os.path.join(destination_directory, location)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Move the file
            shutil.move(file_path, os.path.join(folder_path, file_name))
            print(f'Moved {file_name} to {folder_path}')
        else:
            print(f'File {file_name} not found in {pdf_directory}')
