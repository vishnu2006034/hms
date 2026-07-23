import typing
from flask import abort
from flask_login import current_user

from app.repositories.record_repository import RecordRepository
from app.seed import schema

from hogc.lib.contracts.crud.models import QueryFilter


class VisibilityService:
    """Service to handle role-based data visibility logic."""

    @staticmethod
    def _add_search_filter(filters: list[QueryFilter], search: typing.Optional[str], search_field: str) -> list[QueryFilter]:
        """Add a search filter if a search term is provided."""
        if search and search_field:
            filters.append(QueryFilter(field=search_field, operator="contains", value=search))
        return filters

    @classmethod
    def get_patients(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated patients based on user role."""
        if current_user.role == "Doctor":
            visit_filters = [QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id)]
            visits_resp = RecordRepository.get_records(schema.VISITS_MODULE_ID, page=1, page_size=1000, filters=visit_filters)
            visit_patient_ids = {v.data.get("patient_lookup") for v in visits_resp.items if v.data.get("patient_lookup")}
            
            all_patients = RecordRepository.get_records(schema.PATIENTS_MODULE_ID, page=1, page_size=1000).items
            filtered = []
            for p in all_patients:
                if p.data.get("assigned_doctor") == current_user.hogc_record_id or p.id in visit_patient_ids:
                    if not search or search.lower() in str(p.data.get("first_name", "")).lower() or search.lower() in str(p.data.get("last_name", "")).lower():
                        filtered.append(p)
                        
            from types import SimpleNamespace
            total = len(filtered)
            start = (page - 1) * page_size
            return SimpleNamespace(items=filtered[start:start+page_size], total=total)

        filters: list[QueryFilter] = cls._add_search_filter([], search, "first_name")
        return RecordRepository.get_records(schema.PATIENTS_MODULE_ID, page, page_size, filters)

    @classmethod
    def get_all_patients(cls) -> typing.Any:
        """Fetch all patients available to the user."""
        if current_user.role == "Doctor":
            visit_filters = [QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id)]
            visits_resp = RecordRepository.get_records(schema.VISITS_MODULE_ID, page=1, page_size=1000, filters=visit_filters)
            visit_patient_ids = {v.data.get("patient_lookup") for v in visits_resp.items if v.data.get("patient_lookup")}
            
            all_patients = RecordRepository.get_all_records(schema.PATIENTS_MODULE_ID)
            filtered = []
            for p in all_patients:
                if p.data.get("assigned_doctor") == current_user.hogc_record_id or p.id in visit_patient_ids:
                    filtered.append(p)
            return filtered

        return RecordRepository.get_all_records(schema.PATIENTS_MODULE_ID)

    @classmethod
    def count_patients(cls) -> int:
        """Count total patients available to the user."""
        if current_user.role == "Doctor":
            visit_filters = [QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id)]
            visits_resp = RecordRepository.get_records(schema.VISITS_MODULE_ID, page=1, page_size=1000, filters=visit_filters)
            visit_patient_ids = {v.data.get("patient_lookup") for v in visits_resp.items if v.data.get("patient_lookup")}
            
            all_patients = RecordRepository.get_all_records(schema.PATIENTS_MODULE_ID)
            filtered = []
            for p in all_patients:
                if p.data.get("assigned_doctor") == current_user.hogc_record_id or p.id in visit_patient_ids:
                    filtered.append(p)
            return len(filtered)

        result = RecordRepository.get_records(schema.PATIENTS_MODULE_ID, page=1, page_size=1)
        return result.total

    @classmethod
    def get_visits(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated visits based on user role."""
        if current_user.role in ("Pharmacist", "Lab Technician"):
            return None

        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        
        filters = cls._add_search_filter(filters, search, "visit_id")
        return RecordRepository.get_records(schema.VISITS_MODULE_ID, page, page_size, filters)

    @classmethod
    def count_visits(cls, status: typing.Optional[str] = None) -> int:
        """Count total visits available to the user, optionally filtered by status."""
        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        if status:
            filters.append(QueryFilter(field="status", operator="eq", value=status))
            
        result = RecordRepository.get_records(schema.VISITS_MODULE_ID, page=1, page_size=1, filters=filters)
        return result.total

    @classmethod
    def get_prescriptions(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated prescriptions based on user role."""
        if current_user.role in ("Receptionist", "Lab Technician"):
            return None

        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        
        filters = cls._add_search_filter(filters, search, "medication_name")
        return RecordRepository.get_records(schema.PRESCRIPTIONS_MODULE_ID, page, page_size, filters)

    @classmethod
    def count_prescriptions(cls) -> int:
        """Count total prescriptions available to the user."""
        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
            
        result = RecordRepository.get_records(schema.PRESCRIPTIONS_MODULE_ID, page=1, page_size=1, filters=filters)
        return result.total

    @classmethod
    def get_laboratory_tests(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated laboratory tests based on user role."""
        if current_user.role in ("Receptionist", "Pharmacist"):
            return None

        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        elif current_user.role == "Lab Technician":
            pass
        
        filters = cls._add_search_filter(filters, search, "test_name")
        return RecordRepository.get_records(schema.LABORATORY_MODULE_ID, page, page_size, filters)

    @classmethod
    def get_inventory_items(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated inventory items based on user role."""
        if current_user.role not in ("Pharmacist", "Admin"):
            return None

        filters: list[QueryFilter] = cls._add_search_filter([], search, "item_name")
        return RecordRepository.get_records(schema.INVENTORY_MODULE_ID, page, page_size, filters)

    @classmethod
    def count_inventory_items(cls) -> int:
        """Count total inventory items available to the user."""
        if current_user.role not in ("Pharmacist", "Admin"):
            return 0
        result = RecordRepository.get_records(schema.INVENTORY_MODULE_ID, page=1, page_size=1)
        return result.total

    @classmethod
    def count_laboratory_tests(cls) -> int:
        """Count total laboratory tests available to the user."""
        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
            
        result = RecordRepository.get_records(schema.LABORATORY_MODULE_ID, page=1, page_size=1, filters=filters)
        return result.total
