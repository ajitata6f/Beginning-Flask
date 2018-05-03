from flask import Flask
from flask_script import Manager
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_mail import Mail
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_restful import Api


app = Flask(__name__)
app.config.from_pyfile('../config.cfg')
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
pagedown = PageDown(app)
login_manager = LoginManager(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'index'
api = Api(app)




from application.product import views
