"""Automated integration tests for Pet Adoption Center."""

import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

from pet_adoption_center.auth.session import session
from pet_adoption_center.services.pet_service import pet_service
from pet_adoption_center.services.adoption_service import adoption_service
from pet_adoption_center.services.user_service import user_service
from pet_adoption_center.db.connection import init_db, seed_default_data


def run_tests():
    print("Initializing test environment...")
    init_db()
    seed_default_data()

    # Reset a few pets to available for idempotent testing
    from pet_adoption_center.db.connection import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE pets SET status = 'available' WHERE id IN (1, 2, 3);")
        conn.commit()

    # 1. Test Authentication
    print("Testing auth login...")
    ok, msg = session.login("admin", "admin123")
    assert ok, f"Admin login failed: {msg}"
    assert session.is_authenticated
    assert session.is_admin
    print("  ✓ Admin login verified")

    session.logout()
    assert not session.is_authenticated

    ok, _ = session.login("admin", "wrong_password")
    assert not ok, "Login with wrong password should fail"
    print("  ✓ Password rejection verified")

    # 2. Test Registration
    print("Testing user registration...")
    test_user = "test_adopter_1"
    ok, msg = session.register(
        username=test_user,
        password="secret_password",
        full_name="Alex River",
        email="alex@example.com",
        phone="555-9090",
    )
    # If already registered in a previous run, register might fail with taken, let's handle or login
    if not ok and "already taken" in msg:
        ok, msg = session.login(test_user, "secret_password")
    assert ok, f"User registration/login failed: {msg}"
    assert session.current_user is not None
    assert not session.is_admin
    print("  ✓ Registration & adopter session verified")

    # 3. Test Pet Service
    print("Testing pet catalog & filtering...")
    pets = pet_service.list_pets()
    assert len(pets) >= 6, f"Expected at least 6 pets, got {len(pets)}"

    dogs = pet_service.list_pets(species="Dog")
    assert all(p.species == "Dog" for p in dogs), "Species filter failed"

    avail = pet_service.list_pets(status="available")
    assert all(p.status == "available" for p in avail), "Status filter failed"

    search_res = pet_service.list_pets(search="Barnaby")
    assert len(search_res) >= 1 and search_res[0].name == "Barnaby", "Keyword search failed"
    print("  ✓ Pet search and filtering verified")

    # 4. Test Adoption Flow
    print("Testing adoption application...")
    # Find an available pet
    target_pet = avail[0]
    ok, msg, app_id = adoption_service.submit_application(
        pet_id=target_pet.id,
        user_id=session.current_user.id,
        applicant_name=session.current_user.full_name,
        applicant_phone="555-9090",
        applicant_email="alex@example.com",
        living_space="House with fenced yard",
        has_other_pets=False,
        experience_notes="Experienced dog lover with a quiet home and garden.",
    )
    assert ok, f"Application submission failed: {msg}"
    assert app_id is not None
    print(f"  ✓ Application #{app_id} submitted for pet {target_pet.name}")

    # Check user applications
    user_apps = adoption_service.get_user_applications(session.current_user.id)
    assert any(a.id == app_id for a in user_apps), "Submitted application not found in user apps"
    print("  ✓ User applications tracking verified")

    # 5. Test Admin Review
    print("Testing admin application review...")
    session.login("admin", "admin123")
    assert session.is_admin

    ok, msg = adoption_service.review_application(
        app_id=app_id,
        new_status="approved",
        reviewer_notes="Wonderful home environment. Approved!",
    )
    assert ok, f"Admin review failed: {msg}"

    reviewed_app = adoption_service.get_application_by_id(app_id)
    assert reviewed_app.status == "approved"

    updated_pet = pet_service.get_pet_by_id(target_pet.id)
    assert updated_pet.status == "adopted", "Pet status should transition to 'adopted' upon application approval"
    print("  ✓ Application approval and pet status transition verified")

    # 6. Test Admin Metrics
    metrics = adoption_service.get_adoption_metrics()
    assert metrics["total_pets"] >= 6
    assert metrics["adopted_pets"] >= 1
    assert metrics["total_users"] >= 2
    print("  ✓ Dashboard metrics aggregation verified")

    # 7. Test DBMS Relational Views & Queries
    print("Testing DBMS Views and Pre-built Queries...")
    from pet_adoption_center.services.dbms_service import dbms_service

    for q in dbms_service.get_prebuilt_queries():
        ok, headers, rows, elapsed, err = dbms_service.execute_arbitrary_query(q["sql"])
        assert ok, f"DBMS query '{q['title']}' failed: {err}"
        assert len(headers) > 0
    print("  ✓ All 6 academic DBMS queries executed successfully")

    # 8. Test ACID Transactions
    print("Testing ACID Transaction Atomicity & Rollback...")
    # Failure simulation
    fail_res = dbms_service.demonstrate_acid_transaction(simulate_failure=True)
    assert not fail_res["success"]
    assert fail_res["status"] == "ROLLED BACK"
    print("  ✓ ACID ROLLBACK on integrity check failure verified")

    # Success scenario
    commit_res = dbms_service.demonstrate_acid_transaction(simulate_failure=False)
    assert commit_res["success"]
    assert commit_res["status"] == "COMMITTED"
    print("  ✓ ACID COMMIT and atomic persistence verified")

    # 9. Test Trigger Audit Logs
    logs = dbms_service.get_audit_trail()
    assert len(logs) > 0, "Expected audit trigger entries"
    print(f"  ✓ PL/pgSQL triggers active ({len(logs)} audit events captured)")

    print("\nALL AUTOMATED INTEGRATION TESTS PASSED SUCCESSFULLY! 🚀")


if __name__ == "__main__":
    run_tests()
