import pytest
from app import create_app
from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import (
    CreateModuleRequest,
    CreateFieldRequest,
    AddPicklistOptionRequest,
    CreateRecordRequest,
)
from hogc.lib.contracts.crud.types import FieldType
from hogc.lib.kernel.errors import ValidationError

@pytest.fixture(scope="module")
def app():
    app = create_app()
    with app.app_context():
        yield app

@pytest.fixture(scope="module")
def ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID, 
        org_id=Config.HOGC_ORG_ID, 
        user_id="system", 
        roles=["Admin"]
    )

import uuid

@pytest.fixture(scope="module")
def test_module(app, ctx):
    # Create a test module
    mod_id = uuid.uuid4().hex[:8]
    resp = HOGC.crud.module.create(CreateModuleRequest(
        context=ctx,
        name=f"test_pick_{mod_id}",
        api_name=f"test_pick_{mod_id}",
        label="Test Module",
        plural_label="Test Modules",
        description="For testing picklists"
    ))
    module_id = resp.data.id

    # Create optional picklist
    opt_field = HOGC.crud.field.create(CreateFieldRequest(
        context=ctx,
        module_id=module_id,
        field_name="Optional Picklist",
        api_name="opt_picklist",
        field_type=FieldType.PICKLIST,
        label="Optional Picklist",
        is_required=False,
    ))
    
    # Add options
    HOGC.crud.picklist.add_option(AddPicklistOptionRequest(context=ctx, field_id=opt_field.data.id, value="Option A", label="Option A", display_order=1))
    HOGC.crud.picklist.add_option(AddPicklistOptionRequest(context=ctx, field_id=opt_field.data.id, value="Option B", label="Option B", display_order=2))

    # Create mandatory picklist
    req_field = HOGC.crud.field.create(CreateFieldRequest(
        context=ctx,
        module_id=module_id,
        field_name="Required Picklist",
        api_name="req_picklist",
        field_type=FieldType.PICKLIST,
        label="Required Picklist",
        is_required=True,
    ))

    # Add options
    HOGC.crud.picklist.add_option(AddPicklistOptionRequest(context=ctx, field_id=req_field.data.id, value="Req A", label="Req A", display_order=1))

    return module_id

def test_optional_picklist_left_empty(app, ctx, test_module):
    # Should pass and store None
    req = CreateRecordRequest(
        context=ctx,
        module_id=test_module,
        data={
            "req_picklist": "Req A",
            "opt_picklist": ""  # Empty string submitted from form
        }
    )
    resp = HOGC.crud.record.create(req)
    assert resp.data.data.get("opt_picklist") is None

def test_optional_picklist_with_valid_value(app, ctx, test_module):
    # Should pass and store the value
    req = CreateRecordRequest(
        context=ctx,
        module_id=test_module,
        data={
            "req_picklist": "Req A",
            "opt_picklist": "Option A"
        }
    )
    resp = HOGC.crud.record.create(req)
    assert resp.data.data.get("opt_picklist") == "Option A"

def test_optional_picklist_with_invalid_value(app, ctx, test_module):
    # Should fail with picklist ValidationError
    req = CreateRecordRequest(
        context=ctx,
        module_id=test_module,
        data={
            "req_picklist": "Req A",
            "opt_picklist": "Invalid Option"
        }
    )
    with pytest.raises(ValidationError) as excinfo:
        HOGC.crud.record.create(req)
    assert "opt_picklist" in excinfo.value.field_errors
    assert "is not a valid picklist value" in excinfo.value.field_errors["opt_picklist"][0]

def test_mandatory_picklist_left_empty(app, ctx, test_module):
    # Should fail with required ValidationError
    req = CreateRecordRequest(
        context=ctx,
        module_id=test_module,
        data={
            "req_picklist": "",
            "opt_picklist": "Option A"
        }
    )
    with pytest.raises(ValidationError) as excinfo:
        HOGC.crud.record.create(req)
    assert "req_picklist" in excinfo.value.field_errors
    assert "is required" in excinfo.value.field_errors["req_picklist"][0]

def test_mandatory_picklist_with_invalid_value(app, ctx, test_module):
    # Should fail with picklist ValidationError
    req = CreateRecordRequest(
        context=ctx,
        module_id=test_module,
        data={
            "req_picklist": "Req Invalid",
            "opt_picklist": "Option A"
        }
    )
    with pytest.raises(ValidationError) as excinfo:
        HOGC.crud.record.create(req)
    assert "req_picklist" in excinfo.value.field_errors
    assert "is not a valid picklist value" in excinfo.value.field_errors["req_picklist"][0]

def test_multiple_validation_errors(app, ctx, test_module):
    # Should fail and collect multiple errors
    req = CreateRecordRequest(
        context=ctx,
        module_id=test_module,
        data={
            "req_picklist": "Invalid Req",
            "opt_picklist": "Invalid Opt"
        }
    )
    with pytest.raises(ValidationError) as excinfo:
        HOGC.crud.record.create(req)
    
    assert "req_picklist" in excinfo.value.field_errors
    assert "opt_picklist" in excinfo.value.field_errors
    assert len(excinfo.value.field_errors) == 2
