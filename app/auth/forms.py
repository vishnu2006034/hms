from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.auth.models import AuthUser


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(2, 120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    role = SelectField(
        "Role",
        choices=[
            ("Admin", "Admin"),
            ("Doctor", "Doctor"),
            ("Nurse", "Nurse"),
            ("Pharmacist", "Pharmacist"),
            ("Lab Technician", "Lab Technician"),
        ],
        default="Doctor",
    )
    submit = SubmitField("Register")

    def validate_username(self, field):
        if AuthUser.query.filter_by(username=field.data).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if AuthUser.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")
