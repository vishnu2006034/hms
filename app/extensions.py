import typing

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.login_message = "Please log in to access this page."


@login_manager.user_loader
def load_user(user_id: str) -> typing.Any:
    """Load a user from the database by their session user_id.

    Args:
        user_id: The string representation of the user's primary key,
                 as stored in the session cookie.

    Returns:
        The AuthUser instance matching user_id, or None if not found.
    """
    from app.auth.models import AuthUser
    return db.session.get(AuthUser, int(user_id))


# hogc EAV CRUD Engine
crud = None
SessionLocal = None


def init_crud(database_url: str) -> typing.Any:
    """Initialize the HOGC CRUD engine and expose a structured wrapper on HOGC.crud.

    Creates the SQLAlchemy engine, runs Base.metadata.create_all to ensure all
    HOGC tables exist, then constructs a HOGCCrudWrapper that groups each service
    (records, modules, fields, layouts, picklists, related_records) behind a
    _ServiceProxy for convenient snake_case and alias access.

    Args:
        database_url: A SQLAlchemy-compatible database connection string
                      (e.g. 'postgresql://user:pass@host/db').

    Returns:
        The raw PostgreSQLCRUDProvider instance (also stored in the module-level
        ``crud`` global for legacy access).
    """
    global crud, SessionLocal
    from hogc.engines.crud import PostgreSQLCRUDProvider, Base
    from hogc.lib import HOGC

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    crud = PostgreSQLCRUDProvider(session_factory=SessionLocal)

    HOGC.crud = _HOGCCrudWrapper(crud)

    return crud


class _ServiceProxy:
    """Wrap a HOGC service to expose both snake_case names and short aliases.

    Attribute lookup follows this priority:
    1. Exact match on the underlying service (e.g. ``create_module``).
    2. A predefined alias mapping (e.g. ``link`` → ``link_records``).
    3. Prefixed name  (e.g. ``.create`` → ``create_{prefix}``).
    4. Plural-prefixed name (e.g. ``.list`` → ``list_{prefix}s``).

    Raises:
        AttributeError: If no matching method is found after all lookups.
    """

    _ALIAS_MAP: dict[str, str] = {
        "link": "link_records",
        "unlink": "unlink_records",
        "get_related": "get_related_records",
        "list_for_record": "list_relationships_for_record",
        "add_option": "add_picklist_option",
        "remove_option": "remove_picklist_option",
        "get_options": "get_picklist_options",
        "list_options": "list_picklist_options",
        "import": "import_records",
        "export": "export_records",
        "validate": "validate_import",
    }

    def __init__(self, svc: typing.Any, prefix: str) -> None:
        """Initialize the proxy around a HOGC service.

        Args:
            svc: The raw HOGC service object to wrap.
            prefix: The singular module name used for prefixed attribute lookups
                    (e.g. 'record', 'module', 'field').
        """
        self._svc = svc
        self._prefix = prefix

    def __getattr__(self, name: str) -> typing.Any:
        """Resolve attribute access using exact, alias, prefixed, or plural-prefixed lookup.

        Args:
            name: The attribute name requested by the caller.

        Returns:
            The resolved bound method from the underlying service.

        Raises:
            AttributeError: If no matching method is found.
        """
        if hasattr(self._svc, name):
            return getattr(self._svc, name)

        alias = self._ALIAS_MAP.get(name)
        if alias and hasattr(self._svc, alias):
            return getattr(self._svc, alias)

        prefixed = f"{name}_{self._prefix}"
        if hasattr(self._svc, prefixed):
            return getattr(self._svc, prefixed)

        prefixed_plural = f"{name}_{self._prefix}s"
        if hasattr(self._svc, prefixed_plural):
            return getattr(self._svc, prefixed_plural)

        raise AttributeError(
            f"Service '{type(self._svc).__name__}' has no method '{name}', "
            f"'{prefixed}', or '{prefixed_plural}'"
        )


class _HOGCCrudWrapper:
    """Expose each HOGC service group as a named attribute backed by a _ServiceProxy.

    Attributes:
        record: Proxy over the records service.
        module: Proxy over the modules service.
        field: Proxy over the fields service.
        layout: Proxy over the layouts service.
        picklist: Proxy over the picklists service.
        related_records: Proxy over the related_records service.
        import_export: Proxy over the import/export service.
    """

    def __init__(self, c: typing.Any) -> None:
        """Initialize the wrapper by attaching a _ServiceProxy for each HOGC service.

        Args:
            c: The raw PostgreSQLCRUDProvider instance returned by init_crud.
        """
        self.record = _ServiceProxy(c.records, "record")
        self.module = _ServiceProxy(c.modules, "module")
        self.field = _ServiceProxy(c.fields, "field")
        self.layout = _ServiceProxy(c.layouts, "layout")
        self.picklist = _ServiceProxy(c.picklists, "picklist")
        self.related_records = _ServiceProxy(c.related_records, "related_record")
        self.import_export = _ServiceProxy(c.import_export, "import_export")
        self.seed_crud = c.seed_crud
        self._svc = c
