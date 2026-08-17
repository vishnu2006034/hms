"""Service layer for managing data import and export operations using the HOGC CRUD engine."""
import csv
import io
import json
import os
import tempfile
import typing
from datetime import datetime

from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.models import QueryFilter, RecordQuery
from hogc.lib.contracts.crud.requests import (
    ExportRecordsRequest,
    ImportRecordsRequest,
    ValidateImportRequest,
)
from hogc.lib.contracts.crud.types import ExportFormat, FilterOperator

from app.config import Config
from app.seed import schema


class ImportExportService:
    """Business service layer for CSV and JSON import, validation, template generation, and export."""

    _MODULE_MAP: dict[str, typing.Callable[[], str | None]] = {
        "patients": lambda: schema.PATIENTS_MODULE_ID,
        "visits": lambda: schema.VISITS_MODULE_ID,
        "prescriptions": lambda: schema.PRESCRIPTIONS_MODULE_ID,
        "laboratory": lambda: schema.LABORATORY_MODULE_ID,
        "inventory": lambda: schema.INVENTORY_MODULE_ID,
        "users": lambda: schema.USERS_MODULE_ID,
    }

    _MODULE_CONFIGS: dict[str, dict[str, typing.Any]] = {
        "patients": {
            "name": "patients",
            "label": "Patients",
            "singular_label": "Patient",
            "icon": "bi-people",
            "badge_color": "primary",
            "search_field": "first_name",
            "fields": [
                "first_name",
                "last_name",
                "date_of_birth",
                "age",
                "gender",
                "phone",
                "email",
                "address",
                "blood_group",
                "emergency_contact",
                "emergency_phone",
                "insurance_provider",
                "insurance_id",
                "medical_history",
                "allergies",
                "status",
            ],
            "required_fields": [
                "first_name",
                "last_name",
                "date_of_birth",
                "gender",
                "phone",
                "status",
            ],
            "upsert_candidates": ["email", "phone"],
            "sample_row": {
                "first_name": "Alexander",
                "last_name": "Smith",
                "date_of_birth": "1990-06-15",
                "age": "36",
                "gender": "Male",
                "phone": "+919876543301",
                "email": "alex.smith@example.com",
                "address": "742 Evergreen Terrace, New Delhi",
                "blood_group": "O+",
                "emergency_contact": "Mary Smith (Wife)",
                "emergency_phone": "+919876543302",
                "insurance_provider": "Star Health Insurance",
                "insurance_id": "SH-99201",
                "medical_history": "Mild hypertension",
                "allergies": "Penicillin",
                "status": "Active",
            },
        },
        "inventory": {
            "name": "inventory",
            "label": "Inventory",
            "singular_label": "Inventory Item",
            "icon": "bi-box-seam",
            "badge_color": "warning",
            "search_field": "item_name",
            "fields": [
                "item_name",
                "category",
                "description",
                "quantity",
                "unit",
                "unit_price",
                "supplier",
                "reorder_level",
                "expiry_date",
                "batch_number",
                "location",
                "status",
            ],
            "required_fields": [
                "item_name",
                "category",
                "quantity",
                "unit",
                "unit_price",
                "status",
            ],
            "upsert_candidates": ["item_name", "batch_number"],
            "sample_row": {
                "item_name": "Azithromycin 500mg",
                "category": "Medication",
                "description": "Broad spectrum macrolide antibiotic tablets",
                "quantity": "100",
                "unit": "Strip",
                "unit_price": "85.00",
                "supplier": "Cipla Ltd",
                "reorder_level": "20",
                "expiry_date": "2027-12-31",
                "batch_number": "AZ-2026-01",
                "location": "Pharmacy Store B",
                "status": "In-Stock",
            },
        },
        "visits": {
            "name": "visits",
            "label": "Visits",
            "singular_label": "Visit",
            "icon": "bi-clipboard2-pulse",
            "badge_color": "success",
            "search_field": "chief_complaint",
            "fields": [
                "patient_lookup",
                "doctor_lookup",
                "visit_date",
                "department",
                "chief_complaint",
                "diagnosis",
                "treatment",
                "vitals_bp",
                "vitals_temp",
                "vitals_pulse",
                "vitals_weight",
                "status",
                "symptoms",
                "notes",
            ],
            "required_fields": [
                "patient_lookup",
                "doctor_lookup",
                "visit_date",
                "department",
                "chief_complaint",
                "status",
            ],
            "upsert_candidates": [],
            "sample_row": {
                "patient_lookup": "<patient_record_id>",
                "doctor_lookup": "<doctor_record_id>",
                "visit_date": "2026-08-20T10:00:00",
                "department": "General",
                "chief_complaint": "Persistent headache and fever for 3 days",
                "diagnosis": "Acute viral febrile illness",
                "treatment": "Prescribed Paracetamol 500mg and adequate hydration",
                "vitals_bp": "120/80 mmHg",
                "vitals_temp": "100.4 F",
                "vitals_pulse": "78 bpm",
                "vitals_weight": "70 kg",
                "status": "Completed",
                "symptoms": "Fever,Headache",
                "notes": "Follow up if symptoms persist after 48 hours.",
            },
        },
        "prescriptions": {
            "name": "prescriptions",
            "label": "Prescriptions",
            "singular_label": "Prescription",
            "icon": "bi-capsule",
            "badge_color": "warning",
            "search_field": "medication_name",
            "fields": [
                "patient_lookup",
                "doctor_lookup",
                "visit_lookup",
                "prescribed_date",
                "medication_name",
                "dosage",
                "frequency",
                "duration",
                "instructions",
                "refills",
                "status",
            ],
            "required_fields": [
                "patient_lookup",
                "doctor_lookup",
                "prescribed_date",
                "medication_name",
                "dosage",
                "frequency",
                "duration",
                "status",
            ],
            "upsert_candidates": [],
            "sample_row": {
                "patient_lookup": "<patient_record_id>",
                "doctor_lookup": "<doctor_record_id>",
                "visit_lookup": "<visit_record_id>",
                "prescribed_date": "2026-08-20",
                "medication_name": "Amoxicillin 500mg",
                "dosage": "1 capsule",
                "frequency": "Three times daily",
                "duration": "5 days",
                "instructions": "Take orally after food with water.",
                "refills": "0",
                "status": "Active",
            },
        },
        "laboratory": {
            "name": "laboratory",
            "label": "Laboratory",
            "singular_label": "Lab Test",
            "icon": "bi-lab",
            "badge_color": "info",
            "search_field": "test_name",
            "fields": [
                "patient_lookup",
                "doctor_lookup",
                "visit_lookup",
                "test_name",
                "test_type",
                "priority",
                "sample_date",
                "result_date",
                "result_value",
                "reference_range",
                "status",
                "notes",
                "technician_lookup",
            ],
            "required_fields": [
                "patient_lookup",
                "doctor_lookup",
                "test_name",
                "test_type",
                "priority",
                "sample_date",
                "status",
            ],
            "upsert_candidates": [],
            "sample_row": {
                "patient_lookup": "<patient_record_id>",
                "doctor_lookup": "<doctor_record_id>",
                "visit_lookup": "<visit_record_id>",
                "test_name": "Complete Blood Count (CBC)",
                "test_type": "Blood",
                "priority": "Routine",
                "sample_date": "2026-08-20T11:00:00",
                "result_date": "2026-08-20T15:00:00",
                "result_value": "WBC: 7.2 x10^9/L, Hb: 14.5 g/dL, Platelets: 280 x10^9/L",
                "reference_range": "WBC 4.5-11.0, Hb 13.5-17.5",
                "status": "Completed",
                "notes": "Cell counts within normal reference limits.",
                "technician_lookup": "<technician_record_id>",
            },
        },
        "users": {
            "name": "users",
            "label": "Staff",
            "singular_label": "Staff Member",
            "icon": "bi-person-gear",
            "badge_color": "primary",
            "search_field": "full_name",
            "fields": [
                "full_name",
                "email",
                "phone",
                "role",
                "department",
                "is_active",
            ],
            "required_fields": [
                "full_name",
                "email",
                "role",
            ],
            "upsert_candidates": ["email", "phone"],
            "sample_row": {
                "full_name": "Dr. Clara Barton",
                "email": "clara.barton@hospital.com",
                "phone": "+919876543308",
                "role": "Doctor",
                "department": "Cardiology",
                "is_active": "true",
            },
        },
    }

    @classmethod
    def _build_context(cls) -> RequestContext:
        """Create a system RequestContext for HOGC engine operations.

        Returns:
            A RequestContext populated from current configuration.
        """
        return RequestContext(
            tenant_id=Config.HOGC_TENANT_ID,
            org_id=Config.HOGC_ORG_ID,
            user_id="system",
            roles=["Admin"],
        )

    @classmethod
    def get_module_id(cls, module_name: str) -> str | None:
        """Resolve the module UUID for a given module name.

        Args:
            module_name: Lowercase module name (e.g. 'patients', 'inventory').

        Returns:
            The module UUID string, or None if unknown.
        """
        resolver = cls._MODULE_MAP.get(module_name.lower())
        if resolver is None:
            return None
        return resolver()

    @classmethod
    def get_module_config(cls, module_name: str) -> dict[str, typing.Any] | None:
        """Fetch module UI and import/export configuration.

        Args:
            module_name: Lowercase module name.

        Returns:
            Configuration dictionary containing labels, fields, and sample rows.
        """
        return cls._MODULE_CONFIGS.get(module_name.lower())

    @classmethod
    def list_supported_modules(cls) -> list[dict[str, typing.Any]]:
        """List metadata for all modules supporting import and export.

        Returns:
            List of module configuration dictionaries.
        """
        return list(cls._MODULE_CONFIGS.values())

    @classmethod
    def generate_template_csv(cls, module_name: str) -> str:
        """Generate a starter CSV template containing headers and a sample data row.

        Args:
            module_name: Lowercase module name.

        Returns:
            Raw CSV string content.

        Raises:
            ValueError: If the module is unknown.
        """
        config = cls.get_module_config(module_name)
        if config is None:
            raise ValueError(f"Unknown module '{module_name}'")

        fields: list[str] = config["fields"]
        sample_row: dict[str, str] = config.get("sample_row", {})

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerow(sample_row)
        return output.getvalue()

    @classmethod
    def export_data(
        cls,
        module_name: str,
        export_format: str = "csv",
        search_query: str = "",
        select_fields: list[str] | None = None,
    ) -> tuple[str, str, int]:
        """Export records from the given module to a CSV or JSON file.

        Args:
            module_name: Target module name.
            export_format: 'csv' or 'json'.
            search_query: Optional search keyword to filter exported rows.
            select_fields: Optional list of field API names to export.

        Returns:
            Tuple of (absolute_file_path, suggested_download_filename, record_count).

        Raises:
            ValueError: If module cannot be resolved or export format is invalid.
        """
        module_id: str | None = cls.get_module_id(module_name)
        if module_id is None:
            raise ValueError(f"Module '{module_name}' is not configured or seeded.")

        fmt_enum_str = export_format.lower()
        if fmt_enum_str in ("xls", "xlsx", "excel"):
            fmt_enum = ExportFormat.EXCEL
        elif fmt_enum_str == "csv":
            fmt_enum = ExportFormat.CSV
        else:
            fmt_enum = ExportFormat.JSON

        query: RecordQuery | None = None
        config = cls.get_module_config(module_name)
        if search_query and config:
            search_field = config.get("search_field", "first_name")
            query = RecordQuery(
                module_id=module_id,
                filters=[
                    QueryFilter(
                        field=search_field,
                        operator=FilterOperator.CONTAINS,
                        value=search_query,
                    )
                ],
            )

        fields_to_export = select_fields or (config["fields"] if config else None)

        request = ExportRecordsRequest(
            context=cls._build_context(),
            module_id=module_id,
            format=fmt_enum,
            query=query,
            select_fields=fields_to_export or [],
        )

        response = HOGC.crud.import_export.export_records(request)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        if fmt_enum == ExportFormat.CSV:
            ext = "csv"
        elif fmt_enum == ExportFormat.EXCEL:
            ext = "xlsx"
        else:
            ext = "json"
        download_filename = f"{module_name}_export_{timestamp_str}.{ext}"

        return response.file_url, download_filename, response.record_count

    @classmethod
    def preview_and_validate(
        cls,
        module_name: str,
        file_path: str,
        export_format: str = "csv",
        field_mapping: dict[str, str] | None = None,
    ) -> dict[str, typing.Any]:
        """Read sample rows and run dry-run validation against the CRUD engine.

        Args:
            module_name: Target module name.
            file_path: Absolute path to the uploaded file on disk.
            export_format: 'csv' or 'json'.
            field_mapping: Optional header-to-field mapping dict.

        Returns:
            Dictionary with preview rows, headers, validation status, and error details.
        """
        module_id: str | None = cls.get_module_id(module_name)
        if module_id is None:
            return {
                "success": False,
                "message": f"Module '{module_name}' is not found.",
                "preview_rows": [],
                "headers": [],
                "warnings": [],
                "total_rows": 0,
            }

        fmt_enum_str = export_format.lower()
        if fmt_enum_str in ("xls", "xlsx", "excel"):
            fmt_enum = ExportFormat.EXCEL
        elif fmt_enum_str == "csv":
            fmt_enum = ExportFormat.CSV
        else:
            fmt_enum = ExportFormat.JSON

        # 1. Read first 5 preview rows directly from the file
        headers: list[str] = []
        preview_rows: list[dict[str, typing.Any]] = []
        total_rows: int = 0

        try:
            if fmt_enum == ExportFormat.CSV:
                with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as csv_file:
                    reader = csv.DictReader(csv_file)
                    headers = list(reader.fieldnames or [])
                    for i, row in enumerate(reader):
                        total_rows += 1
                        if i < 5:
                            preview_rows.append(dict(row))
            elif fmt_enum == ExportFormat.JSON:
                with open(file_path, mode="r", encoding="utf-8", errors="replace") as json_file:
                    raw_data = json.load(json_file)
                    items = raw_data if isinstance(raw_data, list) else raw_data.get("data", [])
                    total_rows = len(items)
                    for i, item in enumerate(items):
                        if i == 0 and isinstance(item, dict):
                            headers = list(item.keys())
                        if i < 5 and isinstance(item, dict):
                            preview_rows.append(item)
            elif fmt_enum == ExportFormat.EXCEL:
                import pandas as pd
                df = pd.read_excel(file_path)
                df = df.where(pd.notnull(df), None)
                records = df.to_dict(orient="records")
                total_rows = len(records)
                if records:
                    headers = [str(k) for k in records[0].keys() if k is not None]
                for i, row in enumerate(records):
                    if i < 5:
                        clean_row = {}
                        for k, v in row.items():
                            if k is not None:
                                clean_row[str(k).strip()] = str(v).strip() if isinstance(v, str) else v
                        preview_rows.append(clean_row)
        except Exception as read_err:
            return {
                "success": False,
                "message": f"Could not parse file: {read_err}",
                "preview_rows": [],
                "headers": [],
                "warnings": [str(read_err)],
                "total_rows": 0,
            }

        # 2. Run engine dry-run validation
        val_request = ValidateImportRequest(
            context=cls._build_context(),
            module_id=module_id,
            file_url=file_path,
            format=fmt_enum,
            field_mapping=field_mapping or {},
        )

        try:
            val_response = HOGC.crud.import_export.validate_import(val_request)
            return {
                "success": val_response.success,
                "message": val_response.message,
                "warnings": val_response.warnings or [],
                "preview_rows": preview_rows,
                "headers": headers,
                "total_rows": total_rows,
            }
        except Exception as val_err:
            return {
                "success": False,
                "message": f"Validation error: {val_err}",
                "warnings": [str(val_err)],
                "preview_rows": preview_rows,
                "headers": headers,
                "total_rows": total_rows,
            }

    @classmethod
    def execute_import(
        cls,
        module_name: str,
        file_path: str,
        export_format: str = "csv",
        field_mapping: dict[str, str] | None = None,
        upsert_on: list[str] | None = None,
    ) -> dict[str, typing.Any]:
        """Execute streaming batch import into the target module.

        Args:
            module_name: Target module name.
            file_path: Absolute path to the uploaded file.
            export_format: 'csv' or 'json'.
            field_mapping: Optional header-to-field mapping dict.
            upsert_on: Optional list of field names for matching existing rows.

        Returns:
            Dictionary with import statistics and results.
        """
        module_id: str | None = cls.get_module_id(module_name)
        if module_id is None:
            return {
                "success": False,
                "message": f"Module '{module_name}' is not found.",
                "total_records": 0,
                "succeeded_records": 0,
                "failed_records": 0,
            }

        fmt_enum_str = export_format.lower()
        if fmt_enum_str in ("xls", "xlsx", "excel"):
            fmt_enum = ExportFormat.EXCEL
        elif fmt_enum_str == "csv":
            fmt_enum = ExportFormat.CSV
        else:
            fmt_enum = ExportFormat.JSON

        request = ImportRecordsRequest(
            context=cls._build_context(),
            module_id=module_id,
            file_url=file_path,
            format=fmt_enum,
            field_mapping=field_mapping or {},
            upsert_on=upsert_on or [],
        )

        try:
            response = HOGC.crud.import_export.import_records(request)
            data = response.data
            return {
                "success": response.success,
                "message": response.message,
                "total_records": data.total_records if data else 0,
                "succeeded_records": data.succeeded_records if data else 0,
                "failed_records": data.failed_records if data else 0,
                "status": data.status.value if data and hasattr(data.status, "value") else "COMPLETED",
                "error_file_url": data.error_file_url if data else None,
            }
        except Exception as import_err:
            return {
                "success": False,
                "message": f"Import failed: {import_err}",
                "total_records": 0,
                "succeeded_records": 0,
                "failed_records": 0,
                "status": "FAILED",
                "error_file_url": None,
            }
