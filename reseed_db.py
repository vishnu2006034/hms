import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.seed.schema import _drop_all_hogc
from app.seed import _do_seed

app = create_app()
with app.app_context():
    print("Dropping existing data...")
    _drop_all_hogc()
    print("Seeding new data...")
    _do_seed()
    print("Database successfully reseeded.")
