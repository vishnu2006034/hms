# How the CRUD Engine Works

This project is powered by the **HOGC CRUD Engine** (`hogc-crud-engine`), an **Entity-Attribute-Value (EAV)** platform that lets you define data structures (modules, fields) at runtime — no migrations required. Understanding how it works will help you extend the app or build new modules.

## Core Concepts

| Concept | What it is | Example in HMS |
|---|---|---|
| **Module** | A "table" — a named collection of records | `patients`, `visits`, `inventory` |
| **Field** | A column definition on a module (name, type, constraints) | `first_name` (TEXT), `gender` (PICKLIST) |
| **Record** | A single row of data in a module | One patient, one visit |
| **Picklist** | A set of predefined options for a PICKLIST / MULTI_PICKLIST field | Gender → Male, Female, Other |
| **Layout** | Controls which fields appear and in what order on a form | Default patient form layout |
| **Relationship** | A defined link between two modules | Patient → Visits (one-to-many) |
| **RequestContext** | Auth context passed with every engine call (tenant, org, user, roles) | — |

## Available Field Types

The engine supports the following `FieldType` values:

| Field Type | Description |
|---|---|
| `TEXT` | Plain text string |
| `NUMBER` | Numeric value |
| `BOOLEAN` | True / false |
| `DATE` | Date only |
| `DATETIME` | Date and time |
| `EMAIL` | Email address |
| `PHONE` | Phone number |
| `URL` | Web URL |
| `PICKLIST` | Single-select dropdown |
| `MULTI_PICKLIST` | Multi-select dropdown |
| `LOOKUP` | Foreign key reference to another module |
| `MULTI_LOOKUP` | Multiple foreign key references |
| `FILE` | File attachment |
| `IMAGE` | Image attachment |
| `JSON` | Raw JSON data |
| `FORMULA` | Computed / formula field |
| `CURRENCY` | Currency value |
| `PERCENT` | Percentage value |
| `AUTO_NUMBER` | Auto-incrementing ID (e.g. `PAT-0001`) |

## Project Architecture

The codebase follows a **layered architecture**:

```
Routes (Blueprints)  →  Services  →  Repository / HOGC Facade  →  CRUD Engine
```

| Layer | Location | Responsibility |
|---|---|---|
| **Routes** | `app/modules/` | Handle HTTP requests, render templates |
| **Services** | `app/services/` | Business logic, authorization, visibility |
| **Repository** | `app/repositories/` | Generic CRUD wrapper around `HOGC.crud` |
| **Seed** | `app/seed/` | Schema definitions and initial data |
| **Extensions** | `app/extensions.py` | Engine initialization and `HOGC.crud` setup |

## Setting Up the Engine

The engine is initialized once in `app/extensions.py`:

```python
from hogc.engines.crud import PostgreSQLCRUDProvider, Base
from hogc.lib import HOGC

engine = create_engine(database_url)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
crud = PostgreSQLCRUDProvider(session_factory=SessionLocal)
```

After initialization, all operations go through the **`HOGC.crud`** facade, which exposes:
- `HOGC.crud.module` — Module operations
- `HOGC.crud.field` — Field operations
- `HOGC.crud.record` — Record operations
- `HOGC.crud.picklist` — Picklist operations
- `HOGC.crud.layout` — Layout operations
- `HOGC.crud.related_records` — Relationship operations

## RequestContext

Every engine call requires a `RequestContext` for multi-tenancy and authorization:

```python
from hogc.lib.base import RequestContext

ctx = RequestContext(
    tenant_id="hms",
    org_id="default",
    user_id="system",     # or the current user's ID
    roles=["Admin"],      # user's roles
)
```

## Code Examples

### 1. Creating a Module

```python
from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import CreateModuleRequest

resp = HOGC.crud.module.create(CreateModuleRequest(
    context=ctx,
    name="patients",
    api_name="patients",
    label="Patient",
    plural_label="Patients",
    description="Patient records",
))
module_id = resp.data.id
```

### 2. Adding Fields to a Module

```python
from hogc.lib.contracts.crud.requests import CreateFieldRequest
from hogc.lib.contracts.crud.types import FieldType

# Text field
HOGC.crud.field.create(CreateFieldRequest(
    context=ctx,
    module_id=module_id,
    field_name="First Name",
    api_name="first_name",
    field_type=FieldType.TEXT,
    label="First Name",
    is_required=True,
))

# Picklist field
gender_field = HOGC.crud.field.create(CreateFieldRequest(
    context=ctx,
    module_id=module_id,
    field_name="Gender",
    api_name="gender",
    field_type=FieldType.PICKLIST,
    label="Gender",
    is_required=True,
))

# Lookup field (foreign key to another module)
HOGC.crud.field.create(CreateFieldRequest(
    context=ctx,
    module_id=module_id,
    field_name="Assigned Doctor",
    api_name="assigned_doctor",
    field_type=FieldType.LOOKUP,
    label="Assigned Doctor",
    lookup_module_id=users_module_id,
))
```

### 3. Adding Picklist Options

```python
from hogc.lib.contracts.crud.requests import AddPicklistOptionRequest

HOGC.crud.picklist.add_option(AddPicklistOptionRequest(
    context=ctx,
    field_id=gender_field.data.id,
    value="Male",
    label="Male",
    display_order=0,
))
HOGC.crud.picklist.add_option(AddPicklistOptionRequest(
    context=ctx,
    field_id=gender_field.data.id,
    value="Female",
    label="Female",
    display_order=1,
))
```

### 4. Creating a Record

```python
from hogc.lib.contracts.crud.requests import CreateRecordRequest

resp = HOGC.crud.record.create(CreateRecordRequest(
    context=ctx,
    module_id=module_id,
    data={
        "first_name": "John",
        "last_name": "Doe",
        "gender": "Male",
        "phone": "+1234567890",
        "status": "Active",
    },
))
record_id = resp.data.id
```

### 5. Querying Records

```python
from hogc.lib.contracts.crud.requests import (
    ListRecordsRequest, QueryRecordsRequest, GetRecordRequest,
)
from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter
from hogc.lib.contracts.crud.types import FilterOperator

# List all (paginated)
result = HOGC.crud.record.list(ListRecordsRequest(
    context=ctx, module_id=module_id, page=1, page_size=20,
))
for record in result.items:
    print(record.data)

# Get a single record
resp = HOGC.crud.record.get(GetRecordRequest(
    context=ctx, module_id=module_id, record_id=record_id,
))

# Query with filters
result = HOGC.crud.record.query(QueryRecordsRequest(
    context=ctx,
    query=RecordQuery(
        module_id=module_id,
        filters=[
            QueryFilter(field_api_name="status", operator=FilterOperator.EQ, value="Active"),
        ],
        page=1,
        page_size=20,
    ),
))
```

### 6. Updating and Deleting Records

```python
from hogc.lib.contracts.crud.requests import UpdateRecordRequest, DeleteRecordRequest

# Update
HOGC.crud.record.update(UpdateRecordRequest(
    context=ctx,
    module_id=module_id,
    record_id=record_id,
    data={"status": "Discharged"},
))

# Delete
HOGC.crud.record.delete(DeleteRecordRequest(
    context=ctx,
    module_id=module_id,
    record_id=record_id,
))
```

### 7. Defining Relationships & Linking Records

```python
from hogc.engines.crud.schema import RelationshipDefinition
from hogc.lib.contracts.crud.requests import LinkRecordsRequest, GetRelatedRecordsRequest

# Define a one-to-many relationship (Patient → Visits)
rel = RelationshipDefinition(
    tenant_id="hms",
    org_id="default",
    from_module_id=patients_module_id,
    to_module_id=visits_module_id,
    relationship_type="one_to_many",
)
session.add(rel)
session.commit()

# Link two records
HOGC.crud.related_records.link(LinkRecordsRequest(
    context=ctx,
    relationship_id=rel.id,
    from_record_id=patient_record_id,
    to_record_id=visit_record_id,
))

# Fetch related records
related = HOGC.crud.related_records.get_related(GetRelatedRecordsRequest(
    context=ctx,
    relationship_id=rel.id,
    record_id=patient_record_id,
    page=1,
    page_size=50,
))
for link in related.items:
    print(link.to_record_id)
```

## Adding a New Module (Step-by-Step)

To add a new module to HMS (e.g. "Billing"):

1. **Define the schema** — Add a `_seed_billing_module()` function in `app/seed/schema.py` that creates the module, its fields, and any picklist options.
2. **Wire it into the seed** — Call your function from `_do_seed()` in `app/seed/__init__.py`.
3. **Create a service** — Add `app/services/billing_service.py` with business logic methods that use `HOGC.crud.record` for CRUD operations.
4. **Create a blueprint** — Add `app/modules/billing.py` with Flask routes for list / detail / create / edit / delete views.
5. **Register the blueprint** — Import and register it in `app/__init__.py`.
6. **Add templates** — Create HTML templates under `app/templates/modules/billing/`.
7. **Reset and reseed** — Run `python reset_db.py` to rebuild the database with the new module.
