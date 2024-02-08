import sqlite3
# modules/config.py

class Config:
    SECRET_KEY = 'Is1S3cr3tk3y'
    DEBUG = True

    # File upload configuration
    UPLOAD_FOLDER = './input'
    OUTPUT_FOLDER = './output'
    PROCESSED_FOLDER = './processed'
    TEMP_DOWNLOAD_FOLDER = './output'
    ALLOWED_EXTENSIONS = {'pdf'}

    # Database configuration
    DATABASE = './static/isidatabase.db'

# Database helper functions
def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create the employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT
        );
    ''')

    # Create the task status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS taskstatus (
            id INTEGER PRIMARY KEY,
            status_name TEXT UNIQUE NOT NULL
        );
    ''')

    # Create the task priority table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS taskpriority (
            id INTEGER PRIMARY KEY,
            priority_name TEXT UNIQUE NOT NULL
        );
    ''')

    # Create the task category table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS taskcategory (
            id INTEGER PRIMARY KEY,
            category_name TEXT UNIQUE NOT NULL
        );
    ''')

    # Create the tasks table with foreign key references
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 2,
            category INTEGER,
            assignee_id INTEGER,
            reporter_id INTEGER,
            due_date TEXT,
            attachment TEXT,
            resolution TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(status) REFERENCES taskstatus(id),
            FOREIGN KEY(priority) REFERENCES taskpriority(id),
            FOREIGN KEY(category) REFERENCES taskcategory(id),
            FOREIGN KEY(assignee_id) REFERENCES employees(id),
            FOREIGN KEY(reporter_id) REFERENCES employees(id) 
        );
    ''')
    # Create the comments table with a task_id reference to the tasks table
    cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY,
                        task_id INTEGER,
                        comment TEXT NOT NULL,
                        commenter_id INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                        FOREIGN KEY(commenter_id) REFERENCES employees(id) 
                    );''')
    # Create aecom reports table
    conn.execute('''CREATE TABLE IF NOT EXISTS aecom_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        inspection_ref TEXT,
                        inspection_date TEXT,
                        document_name TEXT,
                        zipname TEXT,
                        business_entity TEXT
                    );''')
    # Create loler inspections table
    conn.execute('''CREATE TABLE IF NOT EXISTS loler_inspections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_name TEXT,
                        report_date TEXT,
                        next_inspection_date TEXT,
                        file_name TEXT,
                        report_count INTEGER
                    );''')
    # Create assets table
    conn.execute('''CREATE TABLE IF NOT EXISTS assets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        isi_number TEXT,
                        device_type TEXT,
                        make_model TEXT,
                        serial_number TEXT,
                        imei TEXT,
                        mac_address TEXT,
                        allocated_user TEXT,
                        date_stamp TEXT DEFAULT CURRENT_TIMESTAMP
                    );''')
    conn.commit()
    conn.close()