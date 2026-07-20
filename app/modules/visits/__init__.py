from flask import Blueprint

visits_bp = Blueprint("visits", __name__, url_prefix="/visits")

from app.modules.visits import routes  # noqa
