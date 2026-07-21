from flask import Flask
from app.config import config
from app.extensions import db, login_manager, init_crud


def _fmt_auto_id(raw_id: str | None, prefix: str, uuid: str = "") -> str:
    """Format an engine auto_number value as a human-readable prefixed ID.

    Args:
        raw_id: The raw auto_number value stored by the engine (e.g. '1', '42').
        prefix: The module prefix to prepend (e.g. 'VST', 'RX', 'LAB').
        uuid: The record UUID, used as fallback when raw_id is absent.

    Returns:
        A formatted ID string like 'VST-0001' or a short UUID fragment fallback.
    """
    if raw_id:
        try:
            return f"{prefix}-{int(raw_id):04d}"
        except (ValueError, TypeError):
            return f"{prefix}-{raw_id}"
    if uuid:
        return f"{prefix}-{uuid[:8].upper()}"
    return f"{prefix}-????"


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)

    # Register template utility for formatting auto_number IDs
    app.jinja_env.globals["fmt_auto_id"] = _fmt_auto_id

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
        from app.api.layout_routes import layout_api_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(patients_bp)
        app.register_blueprint(visits_bp)
        app.register_blueprint(prescriptions_bp)
        app.register_blueprint(laboratory_bp)
        app.register_blueprint(inventory_bp)
        app.register_blueprint(users_bp)
        app.register_blueprint(layout_api_bp)

        from app.seed import seed_modules
        seed_modules(app)

    return app
