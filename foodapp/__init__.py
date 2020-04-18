import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)

# cloud_sql_instance_name = Project_id:region:instance_id
# to connect when the app is deployed  'mysql+pymysql://root:<db_pass>@/<db_name>?unix_socket=/cloudsql/<cloud_sql_instance_name>'
# to connect when the app is deployed  'mysql+pymysql://root:9sG3yrG63F56mFzt@/?unix_socket=/cloudsql/farmerdiary:asia-southeast1:farmerdiary'
# to connect local  'mysql+pymysql://root:<db_pass>@localhost/<db_name>'
# local host db 'mysql+pymysql://root:artapp01@localhost/farmerdiary_main_db'
# password: 9sG3yrG63F56mFzt

UPLOAD_FOLDER = 'static'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:9sG3yrG63F56mFzt@localhost/farmerdiary_main_db'
app.config['SECRET_KEY'] = os.urandom(12).hex()
app.config['SQLALCHEMY_POOL_SIZE'] = 1
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 0
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
margin = 1.15

from foodapp import routes
