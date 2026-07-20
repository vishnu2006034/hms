from flask import Blueprint

prescriptions_bp = Blueprint("prescriptions", __name__, url_prefix="/prescriptions")

from app.modules.prescriptions import routes  # noqa
