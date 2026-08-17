"""Integration and unit tests for Import and Export functionalities."""
import csv
import json
import os
import tempfile
import typing

import pytest
from flask.testing import FlaskClient

from app import create_app
from app.auth.models import AuthUser
from app.config import Config
from app.extensions import db
from app.seed import schema
from app.services.import_export_service import ImportExportService
from hogc.lib.contracts.crud.types import ExportFormat


@pytest.fixture(scope="module")
def app():
    """Create Flask test application context."""
    app_instance = create_app()
    with app_instance.app_context():
        schema._lookup_module_ids()
        yield app_instance


@pytest.fixture(scope="module")
def admin_user(app):
    """Ensure an admin user exists for test authentication."""
    with app.app_context():
        admin = AuthUser.query.filter_by(username="admin").first()
        if admin is None:
            admin = AuthUser(
                username="admin",
                email="admin@hospital.com",
                full_name="System Admin",
                role="Admin",
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
        return admin


@pytest.fixture
def auth_client(app, admin_user) -> FlaskClient:
    """Create test client with active admin session."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_user.id)
        sess["_fresh"] = True
    return client


def test_template_generation_all_modules(app):
    """Starter CSV templates must generate correctly for all supported modules."""
    for mod_name in ["patients", "inventory", "visits", "prescriptions", "laboratory", "users"]:
        template_csv = ImportExportService.generate_template_csv(mod_name)
        assert len(template_csv) > 0

        reader = list(csv.DictReader(template_csv.splitlines()))
        assert len(reader) == 1

        config = ImportExportService.get_module_config(mod_name)
        for req_f in config["required_fields"]:
            assert req_f in reader[0]


def test_export_patients_csv(app):
    """Exporting patients to CSV must create a valid file with records."""
    file_path, filename, count = ImportExportService.export_data(
        module_name="patients",
        export_format="csv",
    )
    try:
        assert os.path.exists(file_path)
        assert filename.endswith(".csv")
        assert count > 0

        with open(file_path, mode="r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            assert len(rows) == count
            assert "first_name" in rows[0]
            assert "last_name" in rows[0]
            assert "phone" in rows[0]
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def test_export_patients_json(app):
    """Exporting patients to JSON must create a valid JSON file."""
    file_path, filename, count = ImportExportService.export_data(
        module_name="patients",
        export_format="json",
    )
    try:
        assert os.path.exists(file_path)
        assert filename.endswith(".json")
        assert count > 0

        with open(file_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == count
            assert "first_name" in data[0]
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def test_export_with_search_filter(app):
    """Exporting with a search query must filter results appropriately."""
    file_path, filename, count = ImportExportService.export_data(
        module_name="patients",
        export_format="csv",
        search_query="Johnathan",
    )
    try:
        assert os.path.exists(file_path)
        assert count >= 1

        with open(file_path, mode="r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            assert len(rows) == count
            assert any(r["first_name"] == "Johnathan" for r in rows)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def test_validate_import_success(app):
    """Valid CSV content must pass dry-run validation."""
    valid_csv = (
        "first_name,last_name,date_of_birth,gender,phone,status\n"
        "Evelyn,Reed,1993-04-12,Female,+919876543881,Active\n"
        "David,Miller,1985-09-22,Male,+919876543882,Active\n"
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as temp_f:
        temp_f.write(valid_csv)
        temp_path = temp_f.name

    try:
        result = ImportExportService.preview_and_validate(
            module_name="patients",
            file_path=temp_path,
            export_format="csv",
        )
        assert result["success"] is True
        assert result["total_rows"] == 2
        assert len(result["preview_rows"]) == 2
        assert len(result["warnings"]) == 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_validate_import_failure(app):
    """Invalid CSV content must return validation warnings."""
    invalid_csv = (
        "last_name,date_of_birth,gender,phone,status\n"
        "NoFirstName,1990-01-01,Alien,+919876543999,Active\n"
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as temp_f:
        temp_f.write(invalid_csv)
        temp_path = temp_f.name

    try:
        result = ImportExportService.preview_and_validate(
            module_name="patients",
            file_path=temp_path,
            export_format="csv",
        )
        assert result["success"] is False
        assert len(result["warnings"]) > 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_import_and_upsert_records(app):
    """Importing new records and upserting existing records by email must succeed."""
    unique_email = "imported.tester@hospital.com"
    initial_csv = (
        "first_name,last_name,date_of_birth,gender,phone,email,status,address\n"
        f"InitialName,Tester,1994-08-10,Male,+919876543777,{unique_email},Active,Initial Address\n"
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as temp_f:
        temp_f.write(initial_csv)
        temp_path = temp_f.name

    try:
        # 1. Insert new record
        res1 = ImportExportService.execute_import(
            module_name="patients",
            file_path=temp_path,
            export_format="csv",
            upsert_on=["email"],
        )
        assert res1["success"] is True
        assert res1["succeeded_records"] == 1
        assert res1["failed_records"] == 0

        # 2. Update existing record with updated address and name
        update_csv = (
            "first_name,last_name,date_of_birth,gender,phone,email,status,address\n"
            f"UpdatedName,Tester,1994-08-10,Male,+919876543777,{unique_email},Active,Updated Suite 500\n"
        )
        with open(temp_path, mode="w", encoding="utf-8") as f:
            f.write(update_csv)

        res2 = ImportExportService.execute_import(
            module_name="patients",
            file_path=temp_path,
            export_format="csv",
            upsert_on=["email"],
        )
        assert res2["success"] is True
        assert res2["succeeded_records"] == 1
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_import_export_http_routes(auth_client):
    """Flask endpoints for hub, template, export, import page, and validate must respond properly."""
    # 1. Data Hub
    resp_hub = auth_client.get("/data/hub")
    assert resp_hub.status_code == 200
    assert b"Data Management Hub" in resp_hub.data

    # 2. Download Template
    resp_tpl = auth_client.get("/data/patients/template")
    assert resp_tpl.status_code == 200
    assert "attachment; filename=patients_template.csv" in resp_tpl.headers.get("Content-Disposition", "")

    # 3. Export CSV
    resp_exp_csv = auth_client.get("/data/patients/export?format=csv")
    assert resp_exp_csv.status_code == 200
    assert resp_exp_csv.mimetype == "text/csv"

    # 4. Export JSON
    resp_exp_json = auth_client.get("/data/patients/export?format=json")
    assert resp_exp_json.status_code == 200
    assert resp_exp_json.mimetype == "application/json"

    # 5. Import Page
    resp_imp_page = auth_client.get("/data/patients/import")
    assert resp_imp_page.status_code == 200
    assert b"Import Patients" in resp_imp_page.data

    # 6. Validate Import AJAX
    csv_bytes = b"first_name,last_name,date_of_birth,gender,phone,status\nAlice,Wonder,1991-01-01,Female,+919999000011,Active\n"
    import io
    data = {
        "file": (io.BytesIO(csv_bytes), "test.csv"),
        "format": "csv",
    }
    resp_val = auth_client.post(
        "/data/patients/validate",
        data=data,
        content_type="multipart/form-data",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert resp_val.status_code == 200
    json_data = resp_val.get_json()
    assert json_data["success"] is True
    assert json_data["total_rows"] == 1
