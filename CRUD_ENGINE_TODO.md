# CRUD Engine Feature & Improvement Roadmap (TODO)

This document tracks features, missing APIs, and architectural improvements identified while integrating the **HOGC CRUD Engine** (`hogc-crud-engine`) into the Hospital Management System (HMS).

---

## 📌 Phase 1: Core Engine Gaps & Database Bypasses (Critical)

- [ ] **1. Native Support for Soft-Deleted Record Querying & Trash View**
  - **Issue**: `RecordService.list_records` and `RecordService.query_records` hardcode `status == 'active'`. HMS had to bypass the engine with raw SQLAlchemy queries in [`routes_base.py: _get_deleted_records()`](file:///v:/crud_engine/hms/app/modules/routes_base.py#L237-L271).
  - **Proposed Solution**:
    - Add `include_deleted: bool = False` and `status: Optional[str] = None` to `ListRecordsRequest` and `RecordQuery`.
    - Add dedicated `RecordService.list_deleted_records(ListDeletedRecordsRequest)` endpoint.
  - **Acceptance Criteria**:
    - [ ] `HOGC.crud.record.list(ListRecordsRequest(..., include_deleted=True))` returns both active and soft-deleted records.
    - [ ] `HOGC.crud.record.list_deleted(...)` returns only records where `status == 'deleted'`.
    - [ ] Remove raw SQL workaround from `routes_base.py`.

- [ ] **2. First-Class `RelationshipDefinitionService` & API**
  - **Issue**: While `RelationshipDefinition` exists as an ORM entity and `RelatedRecordService` handles linking record pairs, there is no service or API to create, query, list, or delete relationship definitions. HMS had to use raw SQL in [`schema.py: _lookup_relationship_ids()`](file:///v:/crud_engine/hms/app/seed/schema.py#L437-L472) and tests.
  - **Proposed Solution**:
    - Implement `RelationshipDefinitionService` with:
      - `create_relationship(CreateRelationshipRequest)`
      - `update_relationship(UpdateRelationshipRequest)`
      - `delete_relationship(DeleteRelationshipRequest)`
      - `get_relationship(GetRelationshipRequest)`
      - `list_relationships(ListRelationshipsRequest)`
    - Expose via `HOGC.crud.relationship` facade.
  - **Acceptance Criteria**:
    - [ ] Modules can declare one-to-one, one-to-many, and many-to-many relationships via standard API requests.
    - [ ] Remove raw SQL queries against `relationship_definitions` table in HMS seed and test scripts.

- [ ] **3. Tenant Maintenance & Data Purge Utility**
  - **Issue**: No clean administrative method exists to wipe or purge a tenant's EAV data during resets or schema rebuilds. HMS had to manually execute multi-table `DELETE FROM` statements in dependency order in [`schema.py: _drop_all_hogc()`](file:///v:/crud_engine/hms/app/seed/schema.py#L389-L407).
  - **Proposed Solution**:
    - Add `AdminService.purge_tenant(PurgeTenantRequest)` or `crud.admin.purge_tenant_data(tenant_id, org_id)`.
  - **Acceptance Criteria**:
    - [ ] Safely cascades and truncates/deletes records, related links, layouts, picklists, fields, and modules for the specified tenant in the correct dependency order.

---

## 📌 Phase 2: High-Level Orchestration & Lookup Automation (High Priority)

- [ ] **4. Automatic Synchronization of Lookups & Related Records**
  - **Issue**: Setting a `LOOKUP` or `MULTI_LOOKUP` field on a record does not automatically create or update entries in the `related_records` table, nor does record deletion clean up dangling relationship links. HMS had to write manual synchronization hooks in [`routes_base.py: _sync_related_record_on_create()`, `_sync_related_record_on_update()`, `_sync_related_record_on_delete()`](file:///v:/crud_engine/hms/app/modules/routes_base.py#L316-L384).
  - **Proposed Solution**:
    - Hook into `RecordService.create_record`, `update_record`, and `delete_record` to automatically create/update/remove `RelatedRecord` junction entries when fields of type `LOOKUP` / `MULTI_LOOKUP` have matching `RelationshipDefinition`s.
  - **Acceptance Criteria**:
    - [ ] Creating a Visit with `patient_lookup="pat-123"` automatically inserts a `RelatedRecord` linking `pat-123` -> `visit-456`.
    - [ ] Deleting a patient or visit cascades and cleans up junction links.
    - [ ] Remove manual sync hooks from HMS `routes_base.py`.

- [ ] **5. Lookup Field Expansion & Display Name Resolution**
  - **Issue**: When records are fetched, `LOOKUP` fields contain only raw UUID strings. HMS had to write [`routes_base.py: _resolve_lookups()`](file:///v:/crud_engine/hms/app/modules/routes_base.py#L131-L164) and [`_get_record_display_name()`](file:///v:/crud_engine/hms/app/modules/routes_base.py#L117-L129) to batch-fetch related records and guess display titles from `first_name`, `full_name`, `name`, etc.
  - **Proposed Solution**:
    - Add `expand_lookups: bool = False` or `expand_fields: list[str] = []` to `GetRecordRequest`, `ListRecordsRequest`, and `QueryRecordsRequest`.
    - Support a configurable `display_field` on `Module` or `Field` (e.g. `module.title_field = "full_name"`).
  - **Acceptance Criteria**:
    - [ ] When `expand_lookups=True`, lookup fields in `RecordDTO.data` include resolved display titles and summary objects (e.g. `{"id": "...", "label": "Dr. Sarah Johnson"}`).

- [ ] **6. Hydrated / Populated Related Records API**
  - **Issue**: `HOGC.crud.related_records.get_related()` only returns junction rows with `from_record_id` and `to_record_id`. Fetching related entities requires N+1 `get_record()` calls (see [`patient_service.py: get_patient_detail()`](file:///v:/crud_engine/hms/app/services/patient_service.py#L62-L100)).
  - **Proposed Solution**:
    - Add `include_record_data: bool = False` to `GetRelatedRecordsRequest`.
    - When enabled, the engine joins/fetches target records and returns a list of hydrated `RecordDTO` objects alongside relationship attributes.
  - **Acceptance Criteria**:
    - [ ] `HOGC.crud.related_records.get_related(GetRelatedRecordsRequest(..., include_record_data=True))` returns populated records in a single query.

- [ ] **7. Bundled Module Metadata API (`get_module_metadata`)**
  - **Issue**: Rendering forms requires module definition, fields, layout, and picklist options. HMS currently makes 3+ separate calls (`field.list`, `layout.list`, and multiple `picklist.get_options`) in [`routes_base.py: get_module_metadata()`](file:///v:/crud_engine/hms/app/modules/routes_base.py#L21-L45).
  - **Proposed Solution**:
    - Add `ModuleService.get_metadata(GetModuleMetadataRequest)` returning a unified `ModuleMetadataResponse` containing:
      - Module details
      - Fields list and type metadata
      - Active layouts
      - Picklist options map `{field_api_name: [PicklistOptionDTO]}`
      - Relationships list
  - **Acceptance Criteria**:
    - [ ] Single API call provides everything needed to dynamically render create/edit forms and table columns.

---

## 📌 Phase 3: Query Engine Enhancements & Ergonomics (Medium Priority)

- [ ] **8. Cross-Module & Relational Query Filters in `RecordQuery`**
  - **Issue**: `RecordQuery` only supports filtering on fields in the same module. Filtering across relationships (e.g. "Patients who have visits with Doctor X") had to be done in Python memory in [`visibility_service.py: get_patients()`](file:///v:/crud_engine/hms/app/services/visibility_service.py#L48-L67).
  - **Proposed Solution**:
    - Support relational filtering syntax in `QueryFilter`, such as:
      - `QueryFilter(field="visits.doctor_lookup", operator=FilterOperator.EQ, value="doc-123")`
      - Or `QueryFilter(related_module="visits", related_field="doctor_lookup", operator=FilterOperator.EQ, value="doc-123")`.
  - **Acceptance Criteria**:
    - [ ] Engine executes SQL subqueries or joins on `related_records` / `lookup` fields.
    - [ ] Eliminates in-memory filtering of large record sets in HMS.

- [ ] **9. Standardized & Unified CRUD Facade Naming**
  - **Issue**: Provider methods are inconsistent (`records.create_record`, `picklists.add_picklist_option`, `related_records.link_records`). HMS had to build [`_ServiceProxy` and `_HOGCCrudWrapper`](file:///v:/crud_engine/hms/app/extensions.py#L66-L163) in `extensions.py` to allow intuitive syntax (`HOGC.crud.record.create()`, `HOGC.crud.picklist.add_option()`, `HOGC.crud.related_records.link()`).
  - **Proposed Solution**:
    - Standardize aliases directly on the engine's service interfaces and `HOGC.crud` facade:
      - `record.create()`, `record.get()`, `record.list()`, `record.update()`, `record.delete()`, `record.query()`
      - `field.create()`, `field.get()`, `field.list()`, `field.update()`, `field.delete()`
      - `layout.create()`, `layout.get()`, `layout.list()`, `layout.update()`, `layout.delete()`
      - `picklist.add_option()`, `picklist.get_options()`, `picklist.remove_option()`
      - `relationship.create()`, `relationship.list()`, `relationship.link()`, `relationship.unlink()`, `relationship.get_related()`
  - **Acceptance Criteria**:
    - [ ] HMS can remove `_ServiceProxy` and `_HOGCCrudWrapper` from `app/extensions.py` and use native facade methods directly.

- [ ] **10. Built-in Import/Export CSV Template Generator**
  - **Issue**: Generating CSV import templates with headers and example values is implemented manually in [`import_export_service.py: generate_template_csv()`](file:///v:/crud_engine/hms/app/services/import_export_service.py#L360-L384).
  - **Proposed Solution**:
    - Add `ImportExportService.generate_template(GenerateTemplateRequest)` supporting CSV and JSON templates derived directly from module field definitions.
  - **Acceptance Criteria**:
    - [ ] Automatically generates template headers, marking required vs optional fields with sample values based on `FieldType`.
