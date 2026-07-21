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

    class HOGCCrudWrapper:
        def __init__(self, c):
            self.record = c.records
            self.module = c.modules
            self.field = c.fields
            self.layout = c.layouts
            self.picklist = c.picklists
            self.related_records = c.related_records

    HOGC.crud = HOGCCrudWrapper(crud)

    return crud
