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
