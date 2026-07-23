import typing
from flask import abort
from flask_login import current_user

from app.config import Config
from app.seed import schema

from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter
from hogc.lib.contracts.crud.requests import ListRecordsRequest, QueryRecordsRequest


class VisibilityService:
    """Service to handle role-based data visibility logic."""

    @staticmethod
    def _get_ctx() -> RequestContext:
        """Construct RequestContext for current user."""
        user_id: str = "system"
        roles: list[str] = []
        try:
            if current_user and current_user.is_authenticated:
                user_id = str(current_user.id)
                roles = [current_user.role]
        except Exception:
            pass
        return RequestContext(
            tenant_id=Config.HOGC_TENANT_ID,
            org_id=Config.HOGC_ORG_ID,
            user_id=user_id,
            roles=roles,
        )

    @staticmethod
    def _add_search_filter(filters: list[QueryFilter], search: typing.Optional[str], search_field: str) -> list[QueryFilter]:
        """Add a search filter if a search term is provided."""
        if search and search_field:
            filters.append(QueryFilter(field=search_field, operator="contains", value=search))
        return filters

    @classmethod
    def get_patients(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated patients based on user role."""
        ctx = cls._get_ctx()
        user_role = getattr(current_user, "role", None) if getattr(current_user, "is_authenticated", False) else None
        hogc_id = getattr(current_user, "hogc_record_id", None) if getattr(current_user, "is_authenticated", False) else None
        if user_role == "Doctor":
            visit_filters = [QueryFilter(field="doctor_lookup", operator="eq", value=hogc_id)]
            visit_query = RecordQuery(module_id=schema.VISITS_MODULE_ID, filters=visit_filters, page=1, page_size=1000)
            visits_resp = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=visit_query))
            visit_patient_ids = {v.data.get("patient_lookup") for v in visits_resp.items if v.data.get("patient_lookup")}
            
            all_patients = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, page=1, page_size=1000)).items
            filtered = []
            for p in all_patients:
                if p.data.get("assigned_doctor") == hogc_id or p.id in visit_patient_ids:
                    if not search or search.lower() in str(p.data.get("first_name", "")).lower() or search.lower() in str(p.data.get("last_name", "")).lower():
                        filtered.append(p)
                        
            from types import SimpleNamespace
            total = len(filtered)
            start = (page - 1) * page_size
            return SimpleNamespace(items=filtered[start:start+page_size], total=total)

        filters: list[QueryFilter] = cls._add_search_filter([], search, "first_name")
        if filters:
            query = RecordQuery(module_id=schema.PATIENTS_MODULE_ID, filters=filters, page=page, page_size=page_size)
            return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        return HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, page=page, page_size=page_size))

    @classmethod
    def get_all_patients(cls) -> typing.Any:
        """Fetch all patients available to the user."""
        ctx = cls._get_ctx()
        user_role = getattr(current_user, "role", None) if getattr(current_user, "is_authenticated", False) else None
        hogc_id = getattr(current_user, "hogc_record_id", None) if getattr(current_user, "is_authenticated", False) else None
        if user_role == "Doctor":
            visit_filters = [QueryFilter(field="doctor_lookup", operator="eq", value=hogc_id)]
            visit_query = RecordQuery(module_id=schema.VISITS_MODULE_ID, filters=visit_filters, page=1, page_size=1000)
            visits_resp = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=visit_query))
            visit_patient_ids = {v.data.get("patient_lookup") for v in visits_resp.items if v.data.get("patient_lookup")}
            
            all_patients = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, page=1, page_size=200)).items
            filtered = []
            for p in all_patients:
                if p.data.get("assigned_doctor") == hogc_id or p.id in visit_patient_ids:
                    filtered.append(p)
            return filtered

        return HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, page=1, page_size=200)).items

    @classmethod
    def count_patients(cls) -> int:
        """Count total patients available to the user."""
        ctx = cls._get_ctx()
        if current_user.role == "Doctor":
            visit_filters = [QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id)]
            visit_query = RecordQuery(module_id=schema.VISITS_MODULE_ID, filters=visit_filters, page=1, page_size=1000)
            visits_resp = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=visit_query))
            visit_patient_ids = {v.data.get("patient_lookup") for v in visits_resp.items if v.data.get("patient_lookup")}
            
            all_patients = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, page=1, page_size=200)).items
            filtered = []
            for p in all_patients:
                if p.data.get("assigned_doctor") == current_user.hogc_record_id or p.id in visit_patient_ids:
                    filtered.append(p)
            return len(filtered)

        result = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, page=1, page_size=1))
        return result.total

    @classmethod
    def get_visits(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated visits based on user role."""
        user_role = getattr(current_user, "role", None) if getattr(current_user, "is_authenticated", False) else None
        hogc_id = getattr(current_user, "hogc_record_id", None) if getattr(current_user, "is_authenticated", False) else None
        if user_role in ("Pharmacist", "Lab Technician"):
            return None

        ctx = cls._get_ctx()
        filters: list[QueryFilter] = []
        if user_role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=hogc_id))
        
        filters = cls._add_search_filter(filters, search, "visit_id")
        if filters:
            query = RecordQuery(module_id=schema.VISITS_MODULE_ID, filters=filters, page=page, page_size=page_size)
            return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        return HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.VISITS_MODULE_ID, page=page, page_size=page_size))

    @classmethod
    def count_visits(cls, status: typing.Optional[str] = None) -> int:
        """Count total visits available to the user, optionally filtered by status."""
        ctx = cls._get_ctx()
        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
        if status:
            filters.append(QueryFilter(field="status", operator="eq", value=status))
            
        if filters:
            query = RecordQuery(module_id=schema.VISITS_MODULE_ID, filters=filters, page=1, page_size=1)
            result = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        else:
            result = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.VISITS_MODULE_ID, page=1, page_size=1))
        return result.total

    @classmethod
    def get_prescriptions(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated prescriptions based on user role."""
        user_role = getattr(current_user, "role", None) if getattr(current_user, "is_authenticated", False) else None
        hogc_id = getattr(current_user, "hogc_record_id", None) if getattr(current_user, "is_authenticated", False) else None
        if user_role in ("Receptionist", "Lab Technician"):
            return None

        ctx = cls._get_ctx()
        filters: list[QueryFilter] = []
        if user_role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=hogc_id))
        
        filters = cls._add_search_filter(filters, search, "medication_name")
        if filters:
            query = RecordQuery(module_id=schema.PRESCRIPTIONS_MODULE_ID, filters=filters, page=page, page_size=page_size)
            return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        return HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PRESCRIPTIONS_MODULE_ID, page=page, page_size=page_size))

    @classmethod
    def count_prescriptions(cls) -> int:
        """Count total prescriptions available to the user."""
        ctx = cls._get_ctx()
        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
            
        if filters:
            query = RecordQuery(module_id=schema.PRESCRIPTIONS_MODULE_ID, filters=filters, page=1, page_size=1)
            result = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        else:
            result = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PRESCRIPTIONS_MODULE_ID, page=1, page_size=1))
        return result.total

    @classmethod
    def get_laboratory_tests(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated laboratory tests based on user role."""
        user_role = getattr(current_user, "role", None) if getattr(current_user, "is_authenticated", False) else None
        hogc_id = getattr(current_user, "hogc_record_id", None) if getattr(current_user, "is_authenticated", False) else None
        if user_role in ("Receptionist", "Pharmacist"):
            return None

        ctx = cls._get_ctx()
        filters: list[QueryFilter] = []
        if user_role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=hogc_id))
        elif user_role == "Lab Technician":
            pass
        
        filters = cls._add_search_filter(filters, search, "test_name")
        if filters:
            query = RecordQuery(module_id=schema.LABORATORY_MODULE_ID, filters=filters, page=page, page_size=page_size)
            return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        return HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.LABORATORY_MODULE_ID, page=page, page_size=page_size))

    @classmethod
    def get_inventory_items(cls, search: typing.Optional[str] = None, page: int = 1, page_size: int = 20) -> typing.Any:
        """Fetch paginated inventory items based on user role."""
        user_role = getattr(current_user, "role", None) if getattr(current_user, "is_authenticated", False) else None
        if getattr(current_user, "is_authenticated", False) and user_role not in ("Pharmacist", "Admin"):
            return None

        ctx = cls._get_ctx()
        filters: list[QueryFilter] = cls._add_search_filter([], search, "item_name")
        if filters:
            query = RecordQuery(module_id=schema.INVENTORY_MODULE_ID, filters=filters, page=page, page_size=page_size)
            return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        return HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.INVENTORY_MODULE_ID, page=page, page_size=page_size))

    @classmethod
    def count_inventory_items(cls) -> int:
        """Count total inventory items available to the user."""
        if current_user.role not in ("Pharmacist", "Admin"):
            return 0
        ctx = cls._get_ctx()
        result = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.INVENTORY_MODULE_ID, page=1, page_size=1))
        return result.total

    @classmethod
    def count_laboratory_tests(cls) -> int:
        """Count total laboratory tests available to the user."""
        ctx = cls._get_ctx()
        filters: list[QueryFilter] = []
        if current_user.role == "Doctor":
            filters.append(QueryFilter(field="doctor_lookup", operator="eq", value=current_user.hogc_record_id))
            
        if filters:
            query = RecordQuery(module_id=schema.LABORATORY_MODULE_ID, filters=filters, page=1, page_size=1)
            result = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        else:
            result = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.LABORATORY_MODULE_ID, page=1, page_size=1))
        return result.total

