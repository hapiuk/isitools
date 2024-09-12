from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    department = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    access_level = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route to create a default profile (run once to setup)
@app.route('/create-default-profile')
def create_default_profile():
    hashed_password = bcrypt.generate_password_hash('password').decode('utf-8')
    default_user = User(
        first_name='John',
        last_name='Doe',
        email='admin@example.com',
        department='IT',
        location='Head Office',
        access_level='Admin',
        password_hash=hashed_password
    )
    db.session.add(default_user)
    db.session.commit()
    flash('Default profile created. You can now log in with admin@example.com / password', 'info')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/test-flash')
def test_flash():
    flash('This is a test flash message!', 'info')
    return redirect(url_for('login'))

@app.route('/test-error')
def test_error():
    flash('This is a test error message!', 'error')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure database and tables are created
    app.run(debug=True)
