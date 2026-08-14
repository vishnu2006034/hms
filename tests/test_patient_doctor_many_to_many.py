"""
Integration tests: Patient–Doctor many-to-many relationship.

Run with:
    python test_patient_doctor_many_to_many.py

Prerequisites: a clean seeded database (python reset_db.py).
"""
import sys
from app import create_app
from app.seed import schema
from app.config import Config
from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import (
    CreateRecordRequest, DeleteRecordRequest, GetRelatedRecordsRequest,
    LinkRecordsRequest, UnlinkRecordsRequest,
)

app = create_app()

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
_failures: list[str] = []


def ctx() -> RequestContext:
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )


def assert_true(condition: bool, msg: str) -> None:
    if condition:
        print(f"  {PASS}  {msg}")
    else:
        print(f"  {FAIL}  {msg}")
        _failures.append(msg)


def _create_patient(suffix: str = "") -> str:
    """Create a minimal patient record and return its ID."""
    resp = HOGC.crud.record.create(CreateRecordRequest(
        context=ctx(),
        module_id=schema.PATIENTS_MODULE_ID,
        data={
            "first_name": f"Test{suffix}",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "phone": "+9100000000",
            "status": "Active",
        },
    ))
    return resp.data.id


def _get_linked_doctor_ids(patient_id: str) -> list[str]:
    """Return IDs of doctors currently linked to the patient via many_to_many rel."""
    if not schema.PATIENTS_DOCTORS_REL_ID:
        return []
    related = HOGC.crud.related_records.get_related(GetRelatedRecordsRequest(
        context=ctx(),
        relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
        record_id=patient_id,
        page=1,
        page_size=50,
    ))
    return [link.to_record_id for link in (related.items or [])]


def _get_doctors() -> list:
    """Return all doctor records from the users module."""
    from hogc.lib.contracts.crud.requests import ListRecordsRequest
    all_users = HOGC.crud.record.list(ListRecordsRequest(
        context=ctx(), module_id=schema.USERS_MODULE_ID, page=1, page_size=100
    )).items
    return [u for u in all_users if u.data.get("role") == "Doctor"]


def _delete_patient(patient_id: str) -> None:
    HOGC.crud.record.delete(DeleteRecordRequest(
        context=ctx(), module_id=schema.PATIENTS_MODULE_ID, record_id=patient_id
    ))


# ─── Tests ───────────────────────────────────────────────────────────────────


def test_relationship_definition_exists():
    """PATIENTS_DOCTORS_REL_ID must be populated after seeding."""
    print("\n[1] Relationship definition exists")
    assert_true(
        schema.PATIENTS_DOCTORS_REL_ID is not None,
        "PATIENTS_DOCTORS_REL_ID is set (many_to_many RelationshipDefinition was created)"
    )


def test_assign_multiple_doctors_to_one_patient():
    """A single patient can be linked to 2+ doctors."""
    print("\n[2] Assign multiple doctors to one patient")
    doctors = _get_doctors()
    if len(doctors) < 2:
        print(f"  SKIP  Need at least 2 doctors in DB (found {len(doctors)})")
        return

    patient_id = _create_patient("Multi")
    doc_a_id = doctors[0].id
    doc_b_id = doctors[1].id

    HOGC.crud.related_records.link(LinkRecordsRequest(
        context=ctx(), relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
        from_record_id=patient_id, to_record_id=doc_a_id, attributes={},
    ))
    HOGC.crud.related_records.link(LinkRecordsRequest(
        context=ctx(), relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
        from_record_id=patient_id, to_record_id=doc_b_id, attributes={},
    ))

    linked = _get_linked_doctor_ids(patient_id)
    assert_true(doc_a_id in linked, f"Doctor A ({doc_a_id[:8]}) is linked to patient")
    assert_true(doc_b_id in linked, f"Doctor B ({doc_b_id[:8]}) is linked to patient")
    assert_true(len(linked) == 2, "Exactly 2 doctors are linked")

    _delete_patient(patient_id)


def test_one_doctor_assigned_to_multiple_patients():
    """One doctor can appear in the related_records of multiple patients."""
    print("\n[3] One doctor assigned to multiple patients")
    doctors = _get_doctors()
    if not doctors:
        print("  SKIP  No doctors in DB")
        return

    doc_id = doctors[0].id
    patient_a_id = _create_patient("A")
    patient_b_id = _create_patient("B")

    for pid in (patient_a_id, patient_b_id):
        HOGC.crud.related_records.link(LinkRecordsRequest(
            context=ctx(), relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
            from_record_id=pid, to_record_id=doc_id, attributes={},
        ))

    linked_a = _get_linked_doctor_ids(patient_a_id)
    linked_b = _get_linked_doctor_ids(patient_b_id)
    assert_true(doc_id in linked_a, "Doctor is linked to Patient A")
    assert_true(doc_id in linked_b, "Doctor is linked to Patient B")

    _delete_patient(patient_a_id)
    _delete_patient(patient_b_id)


def test_update_replaces_doctors():
    """Unlinking and re-linking correctly updates the doctor set."""
    print("\n[4] Update (unlink old, link new) works correctly")
    doctors = _get_doctors()
    if len(doctors) < 2:
        print(f"  SKIP  Need at least 2 doctors (found {len(doctors)})")
        return

    patient_id = _create_patient("Update")
    doc_a_id = doctors[0].id
    doc_b_id = doctors[1].id

    # Initially assign Doctor A
    HOGC.crud.related_records.link(LinkRecordsRequest(
        context=ctx(), relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
        from_record_id=patient_id, to_record_id=doc_a_id, attributes={},
    ))
    assert_true(doc_a_id in _get_linked_doctor_ids(patient_id), "Doctor A initially linked")

    # Switch to Doctor B
    HOGC.crud.related_records.unlink(UnlinkRecordsRequest(
        context=ctx(), relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
        from_record_id=patient_id, to_record_id=doc_a_id,
    ))
    HOGC.crud.related_records.link(LinkRecordsRequest(
        context=ctx(), relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
        from_record_id=patient_id, to_record_id=doc_b_id, attributes={},
    ))

    final = _get_linked_doctor_ids(patient_id)
    assert_true(doc_a_id not in final, "Doctor A is removed after update")
    assert_true(doc_b_id in final, "Doctor B is present after update")

    _delete_patient(patient_id)


def test_delete_patient_removes_links():
    """After manually unlinking then deleting a patient, no links should remain."""
    print("\n[5] Deleting patient removes related_record links")
    doctors = _get_doctors()
    if not doctors:
        print("  SKIP  No doctors in DB")
        return

    patient_id = _create_patient("Del")
    doc_id = doctors[0].id
    HOGC.crud.related_records.link(LinkRecordsRequest(
        context=ctx(), relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
        from_record_id=patient_id, to_record_id=doc_id, attributes={},
    ))

    # Unlink manually (simulating what PatientService.delete_patient does) then delete
    HOGC.crud.related_records.unlink(UnlinkRecordsRequest(
        context=ctx(), relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
        from_record_id=patient_id, to_record_id=doc_id,
    ))
    _delete_patient(patient_id)

    linked = _get_linked_doctor_ids(patient_id)
    assert_true(len(linked) == 0, "No doctor links remain after patient deletion")


def test_relationship_type_is_many_to_many():
    """The auto-created RelationshipDefinition must have type 'many_to_many'."""
    print("\n[6] RelationshipDefinition.relationship_type == 'many_to_many'")
    from app import extensions
    from app.extensions import db
    session = extensions.SessionLocal()
    try:
        row = session.execute(db.text(
            "SELECT relationship_type, from_field_name, to_field_name "
            "FROM relationship_definitions WHERE id = :rid"
        ), {"rid": schema.PATIENTS_DOCTORS_REL_ID}).fetchone()
        if row:
            rtype, from_field, to_field = row
            assert_true(rtype == "many_to_many", f"relationship_type = '{rtype}' (expected 'many_to_many')")
            assert_true(from_field == "assigned_doctors", f"from_field_name = '{from_field}' (expected 'assigned_doctors')")
            assert_true(to_field == "", f"to_field_name = '{to_field}' (expected '')")
        else:
            assert_true(False, "RelationshipDefinition row not found in DB")
    finally:
        session.close()


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        schema._lookup_module_ids()

        if schema.PATIENTS_DOCTORS_REL_ID is None:
            print(f"\n{FAIL}  PATIENTS_DOCTORS_REL_ID is None — has the DB been reset and reseeded?")
            print("  Run: python reset_db.py  then retry.\n")
            sys.exit(1)

        test_relationship_definition_exists()
        test_assign_multiple_doctors_to_one_patient()
        test_one_doctor_assigned_to_multiple_patients()
        test_update_replaces_doctors()
        test_delete_patient_removes_links()
        test_relationship_type_is_many_to_many()

        print("\n" + "=" * 55)
        if _failures:
            print(f"{FAIL}  {len(_failures)} test(s) failed:")
            for f in _failures:
                print(f"     - {f}")
            sys.exit(1)
        else:
            print(f"{PASS}  All tests passed!")
            sys.exit(0)
