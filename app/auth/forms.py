import typing
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.auth.models import AuthUser


def _get_role_choices() -> list[tuple[str, str]]:
    """Fetch role picklist options live from the HOGC users module."""
    try:
        from hogc.lib import HOGC
        from hogc.lib.base import RequestContext
        from hogc.lib.contracts.crud.requests import ListFieldsRequest, GetPicklistOptionsRequest
        from app.config import Config
        from app.seed import schema
        ctx = RequestContext(
            tenant_id=Config.HOGC_TENANT_ID,
            org_id=Config.HOGC_ORG_ID,
            user_id="system",
            roles=["Admin"],
        )
        fields_resp = HOGC.crud.field.list(ListFieldsRequest(context=ctx, module_id=schema.USERS_MODULE_ID))
        for field in (fields_resp.items or []):
            if field.api_name == "role":
                opts_resp = HOGC.crud.picklist.get_options(GetPicklistOptionsRequest(context=ctx, field_id=field.id))
                if opts_resp and opts_resp.items:
                    return [(o.value, o.label) for o in opts_resp.items]
    except Exception:
        pass
    # Fallback in case engine is not yet seeded
    return [
        ("Admin", "Admin"), ("Doctor", "Doctor"), ("Nurse", "Nurse"),
        ("Pharmacist", "Pharmacist"), ("Lab Technician", "Lab Technician"),
        ("Receptionist", "Receptionist"),
    ]


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    """Form for user registration."""
    username = StringField("Username", validators=[DataRequired(), Length(3, 80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(2, 120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    role = SelectField("Role", choices=[], default="Doctor")
    submit = SubmitField("Register")

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.role.choices = _get_role_choices()

    def validate_username(self, field: StringField) -> None:
        """Ensure the username is not already taken."""
        user: typing.Optional[AuthUser] = AuthUser.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError("Username already taken.")

    def validate_email(self, field: StringField) -> None:
        """Ensure the email is not already registered."""
        user: typing.Optional[AuthUser] = AuthUser.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError("Email already registered.")

