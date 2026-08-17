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
    """Check if the current user has create permission for the given module.

    Args:
        module: The module API name (e.g. 'patients', 'visits').

    Returns:
        True if the current user's role is in the module's create allowlist.
    """
    return current_user.role in MODULE_CREATE.get(module, ())


def can_edit(module: str) -> bool:
    """Check if the current user has edit permission for the given module.

    Args:
        module: The module API name (e.g. 'patients', 'visits').

    Returns:
        True if the current user's role is in the module's edit allowlist.
    """
    return current_user.role in MODULE_EDIT.get(module, ())


def can_delete(module: str) -> bool:
    """Check if the current user has delete permission for the given module.

    Args:
        module: The module API name (e.g. 'patients', 'visits').

    Returns:
        True if the current user's role is in the module's delete allowlist.
    """
    return current_user.role in MODULE_DELETE.get(module, ())


def can_view(module: str) -> bool:
    """Check if the current user has view permission for the given module.

    Args:
        module: The module API name (e.g. 'patients', 'visits').

    Returns:
        True if the current user's role is in the module's view allowlist.
    """
    return current_user.role in MODULE_VIEW.get(module, ())


# ── Private Decorator Enforcement Helpers ────────────────────────────────────

def _enforce_admin(f: typing.Callable, args: tuple, kwargs: dict) -> typing.Any:
    """Abort with 403 if the current user is not an authenticated Admin.

    Args:
        f: The wrapped view function.
        args: Positional arguments forwarded to f.
        kwargs: Keyword arguments forwarded to f.

    Returns:
        The result of calling f if the user is authorized.

    Raises:
        HTTPException: 403 if the user is not an Admin.
    """
    if not current_user.is_authenticated or current_user.role != "Admin":
        abort(403)
    return f(*args, **kwargs)


def _enforce_roles(
    f: typing.Callable,
    allowed_roles: tuple[str, ...],
    args: tuple,
    kwargs: dict,
) -> typing.Any:
    """Abort with 403 if the current user's role is not in allowed_roles.

    Args:
        f: The wrapped view function.
        allowed_roles: The set of roles permitted to call f.
        args: Positional arguments forwarded to f.
        kwargs: Keyword arguments forwarded to f.

    Returns:
        The result of calling f if the user is authorized.

    Raises:
        HTTPException: 403 if the user's role is not permitted.
    """
    if not current_user.is_authenticated or current_user.role not in allowed_roles:
        abort(403)
    return f(*args, **kwargs)


def _enforce_module_permission(
    f: typing.Callable,
    permission_map: dict[str, tuple[str, ...]],
    module: str,
    args: tuple,
    kwargs: dict,
) -> typing.Any:
    """Abort with 403 if the current user lacks the required module permission.

    Args:
        f: The wrapped view function.
        permission_map: One of MODULE_CREATE, MODULE_EDIT, or MODULE_DELETE.
        module: The module API name to look up in the permission_map.
        args: Positional arguments forwarded to f.
        kwargs: Keyword arguments forwarded to f.

    Returns:
        The result of calling f if the user is authorized.

    Raises:
        HTTPException: 403 if the user's role is not in the module's allowlist.
    """
    if not current_user.is_authenticated or current_user.role not in permission_map.get(module, ()):
        abort(403)
    return f(*args, **kwargs)


# ── Decorators ───────────────────────────────────────────────────────────────
def admin_required(f: typing.Callable) -> typing.Callable:
    """Decorator: restrict access to Admin role only.

    Args:
        f: The Flask view function to protect.

    Returns:
        A wrapped function that enforces Admin-only access.
    """
    @wraps(f)
    def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        """Delegate to _enforce_admin and forward all arguments."""
        return _enforce_admin(f, args, kwargs)
    return decorated_function


def role_required(*allowed_roles: str) -> typing.Callable:
    """Decorator factory: restrict access to one or more named roles.

    Args:
        *allowed_roles: The role names that are permitted (e.g. 'Doctor', 'Nurse').

    Returns:
        A decorator that wraps a view function with role enforcement.
    """
    def decorator(f: typing.Callable) -> typing.Callable:
        """Wrap f with the role enforcement check."""
        @wraps(f)
        def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            """Delegate to _enforce_roles and forward all arguments."""
            return _enforce_roles(f, allowed_roles, args, kwargs)
        return decorated_function
    return decorator


def module_create_required(module: str) -> typing.Callable:
    """Decorator factory: restrict access to roles with create permission for a module.

    Args:
        module: The module API name to check create permissions for.

    Returns:
        A decorator that wraps a view function with module-create enforcement.
    """
    def decorator(f: typing.Callable) -> typing.Callable:
        """Wrap f with the module create permission check."""
        @wraps(f)
        def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            """Delegate to _enforce_module_permission using MODULE_CREATE."""
            return _enforce_module_permission(f, MODULE_CREATE, module, args, kwargs)
        return decorated_function
    return decorator


def module_edit_required(module: str) -> typing.Callable:
    """Decorator factory: restrict access to roles with edit permission for a module.

    Args:
        module: The module API name to check edit permissions for.

    Returns:
        A decorator that wraps a view function with module-edit enforcement.
    """
    def decorator(f: typing.Callable) -> typing.Callable:
        """Wrap f with the module edit permission check."""
        @wraps(f)
        def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            """Delegate to _enforce_module_permission using MODULE_EDIT."""
            return _enforce_module_permission(f, MODULE_EDIT, module, args, kwargs)
        return decorated_function
    return decorator


def module_delete_required(module: str) -> typing.Callable:
    """Decorator factory: restrict access to roles with delete permission for a module.

    Args:
        module: The module API name to check delete permissions for.

    Returns:
        A decorator that wraps a view function with module-delete enforcement.
    """
    def decorator(f: typing.Callable) -> typing.Callable:
        """Wrap f with the module delete permission check."""
        @wraps(f)
        def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            """Delegate to _enforce_module_permission using MODULE_DELETE."""
            return _enforce_module_permission(f, MODULE_DELETE, module, args, kwargs)
        return decorated_function
    return decorator


def doctor_or_nurse(f: typing.Callable) -> typing.Callable:
    """Decorator: restrict access to Admin, Doctor, or Nurse roles.

    Args:
        f: The Flask view function to protect.

    Returns:
        A wrapped function that enforces Admin/Doctor/Nurse-only access.
    """
    @wraps(f)
    def decorated_function(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        """Delegate to _enforce_roles with Doctor/Nurse/Admin allowlist."""
        return _enforce_roles(f, ("Admin", "Doctor", "Nurse"), args, kwargs)
    return decorated_function
