import typing
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class AuthUser(UserMixin, db.Model):
    """Database model for user authentication."""
    __tablename__ = "auth_users"

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), unique=True, nullable=False)
    email: str = db.Column(db.String(120), unique=True, nullable=False)
    password_hash: str = db.Column(db.String(256), nullable=False)
    full_name: str = db.Column(db.String(120), nullable=False)
    role: str = db.Column(db.String(30), nullable=False, default="Doctor")
    hogc_record_id: typing.Optional[str] = db.Column(db.String(32), nullable=True)
    is_active_user: bool = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __init__(
        self,
        username: str = "",
        email: str = "",
        full_name: str = "",
        role: str = "Doctor",
        password_hash: str = "",
        hogc_record_id: typing.Optional[str] = None,
        is_active_user: bool = True,
        **kwargs: typing.Any,
    ) -> None:
        """Initialize AuthUser instance."""
        super().__init__(**kwargs)
        if username:
            self.username = username
        if email:
            self.email = email
        if full_name:
            self.full_name = full_name
        if role:
            self.role = role
        if password_hash:
            self.password_hash = password_hash
        if hogc_record_id is not None:
            self.hogc_record_id = hogc_record_id
        self.is_active_user = is_active_user


    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the given password against the hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        """Check if the user account is active."""
        return self.is_active_user

    def has_role(self, *roles: str) -> bool:
        """Check if the user has any of the specified roles."""
        return self.role in roles

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<AuthUser {self.username}>"
