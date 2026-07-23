import typing
from functools import wraps
from flask import abort
from flask_login import current_user


# ── Role Constants ───────────────────────────────────────────────────────────
ROLES_ADMIN: tuple[str, ...] = ("Admin",)
ROLES_ALL: tuple[str, ...] = ("Admin", "Doctor", "Nurse", "Pharmacist", "Lab Technician", "Receptionist")


# ── Module Permission Maps ───────────────────────────────────────────────────
MODULE_CREATE: dict[str, tuple[str, ...]] = {
    "patients": ("Admin", "Nurse", "Receptionist"),
    "visits": ("Admin", "Nurse", "Receptionist"),
    "prescriptions": ("Admin", "Doctor", "Pharmacist"),
    "laboratory": ("Admin", "Doctor", "Lab Technician"),
    "inventory": ("Admin", "Pharmacist"),
    "users": ("Admin",),
}

MODULE_EDIT: dict[str, tuple[str, ...]] = {
    "patients": ("Admin", "Nurse", "Receptionist"),
    "visits": ("Admin", "Doctor", "Nurse", "Receptionist"),
    "prescriptions": ("Admin", "Doctor", "Pharmacist"),
    "laboratory": ("Admin", "Doctor", "Lab Technician"),
    "inventory": ("Admin", "Pharmacist"),
    "users": ("Admin",),
}

MODULE_DELETE: dict[str, tuple[str, ...]] = {
    "patients": ("Admin",),
    "visits": ("Admin",),
    "prescriptions": ("Admin",),
    "laboratory": ("Admin",),
    "inventory": ("Admin",),
    "users": ("Admin",),
}

MODULE_VIEW: dict[str, tuple[str, ...]] = {
    "patients": ROLES_ALL,
    "visits": ("Admin", "Doctor", "Nurse", "Receptionist"),
    "prescriptions": ("Admin", "Doctor", "Nurse", "Pharmacist"),
    "laboratory": ("Admin", "Doctor", "Nurse", "Lab Technician"),
    "inventory": ("Admin", "Doctor", "Nurse", "Pharmacist"),
    "users": ("Admin",),
}


# ── Permission Helper Functions ──────────────────────────────────────────────
def can_create(module: str) -> bool:
    """Check if current user can create in the module."""
    return current_user.role in MODULE_CREATE.get(module, ())


def can_edit(module: str) -> bool:
    """Check if current user can edit in the module."""
    return current_user.role in MODULE_EDIT.get(module, ())


def can_delete(module: str) -> bool:
    """Check if current user can delete in the module."""
    return current_user.role in MODULE_DELETE.get(module, ())


def can_view(module: str) -> bool:
    """Check if current user can view in the module."""
    return current_user.role in MODULE_VIEW.get(module, ())


# ── Decorators ───────────────────────────────────────────────────────────────
def admin_required(f: typing.Callable) -> typing.Callable:
    """Require admin role."""
    @wraps(f)
    def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        if not current_user.is_authenticated or current_user.role != "Admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles: str) -> typing.Callable:
    """Require specific roles."""
    def decorator(f: typing.Callable) -> typing.Callable:
        @wraps(f)
        def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            if not current_user.is_authenticated or current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_create_required(module: str) -> typing.Callable:
    """Require create permission for a module."""
    def decorator(f: typing.Callable) -> typing.Callable:
        @wraps(f)
        def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            if not current_user.is_authenticated or current_user.role not in MODULE_CREATE.get(module, ()):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_edit_required(module: str) -> typing.Callable:
    """Require edit permission for a module."""
    def decorator(f: typing.Callable) -> typing.Callable:
        @wraps(f)
        def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            if not current_user.is_authenticated or current_user.role not in MODULE_EDIT.get(module, ()):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_delete_required(module: str) -> typing.Callable:
    """Require delete permission for a module."""
    def decorator(f: typing.Callable) -> typing.Callable:
        @wraps(f)
        def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            if not current_user.is_authenticated or current_user.role not in MODULE_DELETE.get(module, ()):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def doctor_or_nurse(f: typing.Callable) -> typing.Callable:
    """Require doctor or nurse role."""
    @wraps(f)
    def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        if not current_user.is_authenticated or current_user.role not in ("Admin", "Doctor", "Nurse"):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
