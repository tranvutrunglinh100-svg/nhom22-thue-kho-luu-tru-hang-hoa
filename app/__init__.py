from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
    login_manager.login_message_category = 'warning'

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.warehouse import warehouse_bp
    from app.routes.logistics import logistics_bp
    from app.routes.contracts import contracts_bp
    from app.routes.billing import billing_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(warehouse_bp)
    app.register_blueprint(logistics_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(reports_bp)

    return app
