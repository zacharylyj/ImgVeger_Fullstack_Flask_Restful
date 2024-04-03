from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os

db = SQLAlchemy()
# create the Flask app
app = Flask(__name__)
login_manager = LoginManager(app)
app.config['HISTORY_FOLDER'] = os.path.join(app.static_folder, 'history')
if not os.path.exists(app.config['HISTORY_FOLDER']):
    os.makedirs(app.config['HISTORY_FOLDER'])
    print("Created history folder at", app.config['HISTORY_FOLDER'])
app.config['TEMP_FOLDER'] = os.path.join(app.static_folder, 'temp')
if not os.path.exists(app.config['TEMP_FOLDER']):
    os.makedirs(app.config['TEMP_FOLDER'])
    print("Created history folder at", app.config['TEMP_FOLDER'])

bcrypt = Bcrypt(app)

app.config.from_pyfile("config.cfg")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

try:
    if os.environ["FLASK_ENV"] == 'test':
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///testdatabase.db"    
except:
    print("FLASK_ENV not specified, Using main")

    

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
with app.app_context():
    db.init_app(app)
    from .models import User, History
    db.create_all()
    db.session.commit()
    print("Created Database!")

from .api import api_bp
app.register_blueprint(api_bp)

from . import routes