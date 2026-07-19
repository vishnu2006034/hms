from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegisterForm
from app.auth.models import AuthUser
from app.extensions import db, crud
from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import CreateRecordRequest


def _get_ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id=str(current_user.id) if current_user.is_authenticated else "system",
        roles=[current_user.role] if current_user.is_authenticated else [],
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthUser.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash("Logged in successfully!", "success")
            return redirect(next_page or url_for("main.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = AuthUser(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        try:
            from app.modules.seed import USERS_MODULE_ID
            ctx = _get_ctx()
            record = crud.records.create_record(CreateRecordRequest(
                context=ctx,
                module_id=USERS_MODULE_ID,
                data={
                    "full_name": form.full_name.data,
                    "email": form.email.data,
                    "role": form.role.data,
                    "is_active": "true",
                },
            ))
            user.hogc_record_id = record.data.id
            db.session.commit()
        except Exception:
            pass

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
