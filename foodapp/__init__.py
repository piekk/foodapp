import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from datetime import timedelta

app = Flask(__name__)

# cloud_sql_instance_name = Project_id:region:instance_id
# to connect when the app is deployed  'mysql+pymysql://root:<db_pass>@/<db_name>?unix_socket=/cloudsql/<cloud_sql_instance_name>'
# to connect when the app is deployed  'mysql+pymysql://root:artapp01@/?unix_socket=/cloudsql/f-d-2020:asia-southeast1:farmerdiary'
# to connect local  'mysql+pymysql://root:<db_pass>@localhost/<db_name>'
# local host db 'mysql+pymysql://root:artapp01@localhost/farmerdiary_main_db'



#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://'+os.environ.get('DB_USER')+':'+os.environ.get('DB_PASS')+'@/farmerdiary_main_db?unix_socket=/cloudsql/f-d-2020:asia-southeast1:farmerdiary'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:artapp01@localhost/farmerdiary_main_db'
app.config['SECRET_KEY'] = os.urandom(12).hex()
app.config['SQLALCHEMY_POOL_SIZE'] = 1
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 0
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['IMAGE_STORED'] = os.environ.get('BUCKET')

app.config['BUCKET_NAME'] = os.environ.get('BUCKET_NAME')

app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
app.config['SM_KEY'] = os.environ.get('NEXMO_API_KEY')
app.config['SM_SCR'] = os.environ.get('NEXMO_API_SECRET')





db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
margin = 1.22

from foodapp import routes
