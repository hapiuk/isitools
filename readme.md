# Industrial Safety Inspections - UI Overview

## Project Description

This project is a web-based UI designed for Industrial Safety Inspections (ISI), providing a modern and intuitive interface for managing system users, contacts, email settings, and reporting processes. The UI is built using HTML, CSS, and JavaScript, with a consistent, clean design aimed at enhancing the user experience. Future backend development will integrate Python scripts to handle data extraction, processing, and exporting to Excel and PDF formats.

**Note:** The project hosted here contains only dummy data and does not represent real data from ISI operations.

## Features

- **User Management:** View, create, and delete system users with an intuitive interface. User details include First Name, Last Name, Email, Department, Location, and Access Level (Admin/User). The system uses a simple permissions model to ensure that only Admins can perform actions such as creating or deleting users.
- **Contact Management:** Manage system contacts with easy-to-use search and pagination features. Contacts include First Name, Last Name, Email, and Contact Number. The permissions system prevents non-admin users from editing or deleting contacts, ensuring data integrity.
- **Email Settings:** Configure mail server settings including Mail Server, Port, Username, Password, TLS/SSL options, Default Sender Name, and Email. Save functionality includes visual feedback on changes, with buttons activating only when there are modifications.
- **Report Processing:** Process and view reports for PUWER, LOLER, and Custom Client Reports, with functionalities to upload files, process data, and view historic reports. Each report type has a dedicated modal for streamlined data handling.
- **System Settings:** Access system configurations through settings for users, contacts, and mail settings, all presented in a consistent modal format. A dedicated button within the settings allows Admins to add new users directly from the UI.
- **Flash Messages:** Provides feedback and error handling through dismissible flash messages, styled to fit within the application theme, enhancing the user interaction experience.
- **Responsive Design:** Consistent look and feel across devices, with a footer that remains fixed at the bottom of the viewport, ensuring a seamless experience on both desktop and mobile devices.

## Permissions System

- **Admin Users:** Can view, create, edit, and delete users and contacts. Admins have full control over system settings and configuration.
- **Non-Admin Users:** Can view system users and contacts but cannot create, edit, or delete entries. Attempting to perform restricted actions results in a flash message indicating lack of permission.

## Upcoming Features (Backend Development)

The backend will be developed using Python and will include the following functionalities:

- **Data Extraction:** Scripts to extract data from various sources, ensuring accurate and timely data availability.
- **Data Processing:** Processing the extracted data and formatting it for export.
- **Excel and PDF Export:** Exporting the processed data into Excel files with accompanying PDF reports for comprehensive data presentation.
- **Integration with UI:** Backend scripts will be integrated with the UI to handle real-time data processing and reporting based on user actions within the application.

## Installation

To set up the project locally:

1. Clone the repository:

    ```bash
    git clone https://github.com/hapiuk/isitools.git
    ```

2. Navigate into the project directory:

    ```bash
    cd isitools
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the application:

    ```bash
    flask run
    ```

## Usage

- Access the application via the local server (e.g., `http://127.0.0.1:5000/`).
- Log in using the default admin credentials (or create a user through the admin interface).
- Navigate through the dashboard to access different sections like user management, contacts, and system settings.
- Use the modals to update configurations and manage data. Admin-specific features are clearly marked and accessible based on permissions.

## Contact

For further updates or modifications, please contact:
- **Aaron Gomm**: [LinkedIn](https://www.linkedin.com/in/aaron-gomm-b8880868/)
