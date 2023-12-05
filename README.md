# ISI Dashboard 

This project is a Flask-based web application that allows users to upload PDF files, processes these files, stores and retrieves quiz results, and downloads processed files.

## Installation

This project requires Python 3.6 or later. Clone the repository and install the required packages:

```
git clone https://github.com/aarongommisi/isidashboard.git
cd isidashboard
pip install -r requirements.txt

```

# Usage

## app.py

This script runs the main application. It serves the HTML pages, handles the file upload, processes these files with a separate script, and allows users to download the results.

```
python app.py
```

## pdfextract.py

This script is used to extract data from uploaded PDFs. It extracts specific information from the text of the PDFs, writes this extracted information to a CSV file, merges processed and faulty PDFs into separate files, and moves the processed PDFs to a separate folder.

```
python pdfextract.py --input input_folder --output output_folder --processed processed_folder --business_entity business_entity
```

*Note: Replace input_folder, output_folder, processed_folder, and business_entity with your actual parameters.*


# Web Pages


## index.html

This is the main dashboard of the application. It provides links to other resources or parts of the application such as the Company Website, Service Sight, Lucid App, PDF Data Extraction Tool, Remedial Actions CSV Generator, Incident Report CSV Generator, Suggestion Request, Support Request, SAFED Mock Test, and Leaderboard.

## upload.html

This page allows users to upload PDF files to be processed. Users are also required to provide a business entity name. The page includes a JavaScript script that handles form submission, sends the uploaded files and business entity name to the server, and redirects the user to download the processed files.

## mockexam.html

This page contains the SAFED Mock Test for LOLER (WiP). It includes functionality for displaying questions, selecting answers, calculating scores, and generating certificates.

## leaderboard.html

This page displays the leaderboard for the mock exam. It shows the rank, name, score, total questions, and percentage for each participant.





