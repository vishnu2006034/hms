"""Reset the database so seed data runs fresh on next app start."""
import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

db_url = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/hms")
engine = create_engine(db_url)

with engine.connect() as conn:
    # Drop HOGC EAV tables data
    for table in ["related_records", "relationship_definitions",
                  "picklist_options", "records", "layouts", "fields", "modules"]:
        conn.execute(text(f"DELETE FROM {table} WHERE tenant_id = 'hms'"))

    # Drop auth users (except nothing - clear all for fresh seed)
    conn.execute(text("DELETE FROM auth_users"))

    conn.commit()
    print("Database reset complete. Restart the app to seed fresh data.")
