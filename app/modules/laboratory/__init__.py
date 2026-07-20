from flask import Blueprint

laboratory_bp = Blueprint("laboratory", __name__, url_prefix="/laboratory")

from app.modules.laboratory import routes  # noqa
