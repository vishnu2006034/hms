from flask_login import current_user
from flask import abort
from hogc.lib.contracts.crud.models import QueryFilter
from app.seed import schema
from app.repositories.record_repository import RecordRepository


class VisibilityService:
    """Service to handle role-based data visibility logic."""

    @staticmethod
    def _add_search_filter(filters, search, search_field):
        if search and search_field:
            filters.append(QueryFilter(field=search_field, operator="contains", value=search))
        return filters

    @classmethod
    def get_patients(cls, search=None, page=1, page_size=20):
        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="assigned_doctor", operator="eq", value=current_user.hogc_record_id))
        
        filters = cls._add_search_filter(filters, search, "first_name")
        return RecordRepository.get_records(schema.PATIENTS_MODULE_ID, page, page_size, filters)

    @classmethod
    def get_all_patients(cls):
        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="assigned_doctor", operator="eq", value=current_user.hogc_record_id))
        return RecordRepository.get_all_records(schema.PATIENTS_MODULE_ID, filters=filters)

    @classmethod
    def count_patients(cls):
        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="assigned_doctor", operator="eq", value=current_user.hogc_record_id))
        result = RecordRepository.get_records(schema.PATIENTS_MODULE_ID, page=1, page_size=1, filters=filters)
        return result.total

    @classmethod
    def get_visits(cls, search=None, page=1, page_size=20):
        if current_user.role in ("Pharmacist", "Lab Technician"):
            return None  # Will be handled by the route, or we can just return empty, but better to abort in routes if needed

        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        
        filters = cls._add_search_filter(filters, search, "visit_id")
        return RecordRepository.get_records(schema.VISITS_MODULE_ID, page, page_size, filters)

    @classmethod
    def count_visits(cls, status=None):
        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        if status:
            filters.append(QueryFilter(field="status", operator="eq", value=status))
            
        result = RecordRepository.get_records(schema.VISITS_MODULE_ID, page=1, page_size=1, filters=filters)
        return result.total

    @classmethod
    def get_prescriptions(cls, search=None, page=1, page_size=20):
        if current_user.role in ("Receptionist", "Lab Technician"):
            return None

        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        
        filters = cls._add_search_filter(filters, search, "medication_name")
        return RecordRepository.get_records(schema.PRESCRIPTIONS_MODULE_ID, page, page_size, filters)

    @classmethod
    def count_prescriptions(cls):
        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
            
        result = RecordRepository.get_records(schema.PRESCRIPTIONS_MODULE_ID, page=1, page_size=1, filters=filters)
        return result.total

    @classmethod
    def get_laboratory_tests(cls, search=None, page=1, page_size=20):
        if current_user.role in ("Receptionist", "Pharmacist"):
            return None

        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        elif current_user.role == "Lab Technician":
            # Lab Technicians can see all lab tests. If they only see assigned ones, we'd filter here.
            # "Assigned laboratory work"
            pass
        
        filters = cls._add_search_filter(filters, search, "test_name")
        return RecordRepository.get_records(schema.LABORATORY_MODULE_ID, page, page_size, filters)

    @classmethod
    def get_inventory_items(cls, search=None, page=1, page_size=20):
        if current_user.role not in ("Pharmacist", "Admin"):
            return None

        filters = cls._add_search_filter([], search, "item_name")
        return RecordRepository.get_records(schema.INVENTORY_MODULE_ID, page, page_size, filters)

    @classmethod
    def count_inventory_items(cls):
        if current_user.role not in ("Pharmacist", "Admin"):
            return 0
        result = RecordRepository.get_records(schema.INVENTORY_MODULE_ID, page=1, page_size=1)
        return result.total

    @classmethod
    def count_laboratory_tests(cls):
        filters = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
            
        result = RecordRepository.get_records(schema.LABORATORY_MODULE_ID, page=1, page_size=1, filters=filters)
        return result.total
