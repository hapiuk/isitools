# create_admin.py

from app import app, db, User
import sys

def create_admin():
    with app.app_context():
        # Check if an admin user already exists
        if User.query.filter_by(email='admin@example.com').first():
            print('Admin user already exists.')
            return

        # Create a new admin user
        admin = User(
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
            department='IT',
            location='Head Office',
            access_level='Admin'
        )
        admin.set_password('admin123')  # Set a default password

        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully.')

if __name__ == '__main__':
    create_admin()
