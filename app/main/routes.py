from hogc.lib import HOGC
from flask import render_template
from flask_login import login_required, current_user
from app.main import main_bp

from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import ListRecordsRequest
import app.seed.schema as seed


def _get_ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id=str(current_user.id),
        roles=[current_user.role],
    )


@main_bp.route("/")
@login_required
def dashboard():
    ctx = _get_ctx()
    stats = {"patients": 0, "visits": 0, "inventory": 0, "lab": 0, "prescriptions": 0}

    from app.services.visibility_service import VisibilityService

    try:
        stats["patients"] = VisibilityService.count_patients()
        stats["visits"] = VisibilityService.count_visits()
        stats["inventory"] = VisibilityService.count_inventory_items()
        stats["prescriptions"] = VisibilityService.count_prescriptions()
        stats["lab"] = VisibilityService.count_laboratory_tests()
    except Exception as e:
        print(f"Error fetching stats: {e}")

    return render_template("main/dashboard.html", stats=stats)
