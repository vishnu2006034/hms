"""Database reset and re-seed utility script."""
from app import create_app
from app.extensions import db
from hogc.engines.crud import Base as HogcBase
from app.seed import _do_seed
from sqlalchemy import text


def reset_and_reseed() -> None:
    """Drops all tables from the database and reseeds all modules and initial data."""
    app = create_app()
    with app.app_context():
        print("Dropping all tables from database...")
        with db.engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.commit()

        print("Recreating database tables...")
        HogcBase.metadata.create_all(db.engine)
        db.create_all()

        print("Seeding initial modules and data...")
        _do_seed()
        print("Database reset and reseed completed successfully!")


if __name__ == "__main__":
    reset_and_reseed()
