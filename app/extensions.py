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
def load_user(user_id):
    from app.auth.models import AuthUser
    return AuthUser.query.get(int(user_id))


# hogc EAV CRUD Engine
crud = None
SessionLocal = None


def init_crud(database_url):
    global crud, SessionLocal
    from hogc.engines.crud import PostgreSQLCRUDProvider, Base
    from hogc.lib import HOGC

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    crud = PostgreSQLCRUDProvider(session_factory=SessionLocal)

    class _ServiceProxy:
        """Wrap a service to expose both the snake_case names and short aliases."""
        def __init__(self, svc, prefix: str):
            self._svc = svc
            self._prefix = prefix

        def __getattr__(self, name: str):
            # Try exact name first (e.g. create_module, list_modules)
            if hasattr(self._svc, name):
                return getattr(self._svc, name)
            # Custom mappings for related records and picklists
            mapping = {
                "link": "link_records",
                "unlink": "unlink_records",
                "get_related": "get_related_records",
                "list_for_record": "list_relationships_for_record",
                "add_option": "add_picklist_option",
                "remove_option": "remove_picklist_option",
                "get_options": "get_picklist_options",
                "list_options": "list_picklist_options",
            }
            if name in mapping and hasattr(self._svc, mapping[name]):
                return getattr(self._svc, mapping[name])

            # Try prefixed name (e.g. .create → create_{prefix}, .list → list_{prefix}s, .get → get_{prefix})
            prefixed = f"{name}_{self._prefix}"
            if hasattr(self._svc, prefixed):
                return getattr(self._svc, prefixed)
            # Try with plural (list_modules, list_fields, etc.)
            prefixed_plural = f"{name}_{self._prefix}s"
            if hasattr(self._svc, prefixed_plural):
                return getattr(self._svc, prefixed_plural)
            raise AttributeError(
                f"Service '{type(self._svc).__name__}' has no method '{name}', "
                f"'{prefixed}', or '{prefixed_plural}'"
            )

    class HOGCCrudWrapper:
        def __init__(self, c):
            self.record = _ServiceProxy(c.records, "record")
            self.module = _ServiceProxy(c.modules, "module")
            self.field = _ServiceProxy(c.fields, "field")
            self.layout = _ServiceProxy(c.layouts, "layout")
            self.picklist = _ServiceProxy(c.picklists, "picklist")
            self.related_records = _ServiceProxy(c.related_records, "related_record")

    HOGC.crud = HOGCCrudWrapper(crud)

    return crud
