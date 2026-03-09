from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)

# Config
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cineverse-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:"
    f"{os.getenv('DB_PASSWORD', '')}@"
    f"{os.getenv('DB_HOST', 'localhost')}/"
    f"{os.getenv('DB_NAME', 'cineverse_db')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Mail Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_EMAIL')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Extensions
db = SQLAlchemy(app)
from flask_mail import Mail
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created!")
    app.run(debug=True)