import typing
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegisterForm
from app.auth.models import AuthUser
from app.extensions import db
from app.config import Config

from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import CreateRecordRequest


def _get_ctx() -> RequestContext:
    """Generate RequestContext for current user."""
    user_id: str = str(current_user.id) if current_user.is_authenticated else "system"
    roles: list[str] = [current_user.role] if current_user.is_authenticated else []
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id=user_id,
        roles=roles,
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> typing.Any:
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    
    form: LoginForm = LoginForm()
    if form.validate_on_submit():
        user: typing.Optional[AuthUser] = AuthUser.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember.data)
            next_page: typing.Optional[str] = request.args.get("next")
            flash("Logged in successfully!", "success")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("main.dashboard"))
        
        flash("Invalid username or password.", "danger")
        
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register() -> typing.Any:
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
        
    form: RegisterForm = RegisterForm()
    if form.validate_on_submit():
        user: AuthUser = AuthUser(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        try:
            from app.seed.schema import USERS_MODULE_ID as _uid
            ctx: RequestContext = _get_ctx()
            req: CreateRecordRequest = CreateRecordRequest(
                context=ctx,
                module_id=_uid,
                data={
                    "full_name": form.full_name.data,
                    "email": form.email.data,
                    "role": form.role.data,
                    "is_active": "true",
                },
            )
            record: typing.Any = HOGC.crud.record.create(req)
            user.hogc_record_id = record.data.id
            db.session.commit()
        except Exception:
            pass

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))
        
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout() -> typing.Any:
    """Handle user logout."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
