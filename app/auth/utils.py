from functools import wraps
from flask import abort
from flask_login import current_user


# ── Role Constants ───────────────────────────────────────────────────────────
ROLES_ADMIN = ("Admin",)
ROLES_ALL = ("Admin", "Doctor", "Nurse", "Pharmacist", "Lab Technician", "Receptionist")


# ── Module Permission Maps ───────────────────────────────────────────────────
MODULE_CREATE = {
    "patients": ("Admin", "Doctor", "Nurse", "Receptionist"),
    "visits": ("Admin", "Doctor", "Nurse", "Receptionist"),
    "prescriptions": ("Admin", "Doctor", "Pharmacist"),
    "laboratory": ("Admin", "Doctor", "Lab Technician"),
    "inventory": ("Admin", "Pharmacist"),
    "users": ("Admin",),
}

MODULE_EDIT = {
    "patients": ("Admin", "Doctor", "Nurse", "Receptionist"),
    "visits": ("Admin", "Doctor", "Nurse", "Receptionist"),
    "prescriptions": ("Admin", "Doctor", "Pharmacist"),
    "laboratory": ("Admin", "Doctor", "Lab Technician"),
    "inventory": ("Admin", "Pharmacist"),
    "users": ("Admin",),
}

MODULE_DELETE = {
    "patients": ("Admin",),
    "visits": ("Admin",),
    "prescriptions": ("Admin",),
    "laboratory": ("Admin",),
    "inventory": ("Admin",),
    "users": ("Admin",),
}

MODULE_VIEW = {
    "patients": ROLES_ALL,
    "visits": ("Admin", "Doctor", "Nurse", "Receptionist"),
    "prescriptions": ("Admin", "Doctor", "Nurse", "Pharmacist"),
    "laboratory": ("Admin", "Doctor", "Nurse", "Lab Technician"),
    "inventory": ("Admin", "Doctor", "Nurse", "Pharmacist"),
    "users": ("Admin",),
}


# ── Permission Helper Functions ──────────────────────────────────────────────
def can_create(module):
    return current_user.role in MODULE_CREATE.get(module, ())


def can_edit(module):
    return current_user.role in MODULE_EDIT.get(module, ())


def can_delete(module):
    return current_user.role in MODULE_DELETE.get(module, ())


def can_view(module):
    return current_user.role in MODULE_VIEW.get(module, ())


# ── Decorators ───────────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "Admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_create_required(module):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in MODULE_CREATE.get(module, ()):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_edit_required(module):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in MODULE_EDIT.get(module, ()):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_delete_required(module):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in MODULE_DELETE.get(module, ()):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def doctor_or_nurse(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ("Admin", "Doctor", "Nurse"):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
