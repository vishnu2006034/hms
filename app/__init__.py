from flask import Flask
from app.config import config
from app.extensions import db, login_manager, init_crud


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        init_crud(app.config["SQLALCHEMY_DATABASE_URI"])

        from app.auth import auth_bp
        from app.main import main_bp
        from app.modules.patients import patients_bp
        from app.modules.visits import visits_bp
        from app.modules.prescriptions import prescriptions_bp
        from app.modules.laboratory import laboratory_bp
        from app.modules.inventory import inventory_bp
        from app.modules.users import users_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(patients_bp)
        app.register_blueprint(visits_bp)
        app.register_blueprint(prescriptions_bp)
        app.register_blueprint(laboratory_bp)
        app.register_blueprint(inventory_bp)
        app.register_blueprint(users_bp)

        from app.seed import seed_modules
        seed_modules(app)

    return app
