from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Inisialisasi SQLAlchemy
db = SQLAlchemy()

# Inisialisasi Login Manager
login_manager = LoginManager()
login_manager.login_view = "login"