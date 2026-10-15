"""Flask Web Application for PawHaven Pet Adoption Center."""

from __future__ import annotations

import functools
import os
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..auth.hasher import hash_password, verify_password
from ..db.connection import get_connection, init_db, seed_default_data, test_connection
from ..models.pet import Pet
from ..models.user import User
from ..services.adoption_service import adoption_service
from ..services.dbms_service import dbms_service
from ..services.pet_service import pet_service
from ..services.user_service import user_service


# Curated high-res animal photos for pets
PET_PHOTO_MAP = {
    "barnaby": "https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=800&q=80",
    "luna": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=800&q=80",
    "mochi": "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?auto=format&fit=crop&w=800&q=80",
    "bella": "https://images.unsplash.com/photo-1537151625747-768eb6cf92b2?auto=format&fit=crop&w=800&q=80",
    "oliver": "https://images.unsplash.com/photo-1573865526739-10659fec78a5?auto=format&fit=crop&w=800&q=80",
    "daisy": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?auto=format&fit=crop&w=800&q=80",
    "pip": "https://images.unsplash.com/photo-1552728089-57bdde30beb3?auto=format&fit=crop&w=800&q=80",
    "ziggy": "https://images.unsplash.com/photo-1554455863-71a2a50a2569?auto=format&fit=crop&w=800&q=80",
}

SPECIES_FALLBACK_MAP = {
    "dog": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=800&q=80",
    "cat": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?auto=format&fit=crop&w=800&q=80",
    "rabbit": "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?auto=format&fit=crop&w=800&q=80",
    "bird": "https://images.unsplash.com/photo-1552728089-57bdde30beb3?auto=format&fit=crop&w=800&q=80",
    "hamster": "https://images.unsplash.com/photo-1548767797-d8c844163c4c?auto=format&fit=crop&w=800&q=80",
}


def get_pet_image(pet: Pet | dict) -> str:
    name = (pet.name if isinstance(pet, Pet) else pet.get("name", "")).strip().lower()
    species = (pet.species if isinstance(pet, Pet) else pet.get("species", "")).strip().lower()

    if name in PET_PHOTO_MAP:
        return PET_PHOTO_MAP[name]
    for key, url in SPECIES_FALLBACK_MAP.items():
        if key in species:
            return url
    return "https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=800&q=80"


def create_app() -> Flask:
    """Application factory for PawHaven Flask WebUI."""
    template_dir = Path(__file__).resolve().parent / "templates"
    static_dir = Path(__file__).resolve().parent / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pawhaven-secret-key-development-2026")

    # Ensure DB is ready
    try:
        init_db()
        seed_default_data()
    except Exception as exc:
        app.logger.warning("DB auto-init warning: %s", exc)

    # ---------------- Auth Helpers ---------------- #
    def get_current_user() -> User | None:
        user_id = session.get("user_id")
        if not user_id:
            return None
        return user_service.get_user_by_id(user_id)

    def login_required(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapped_view(*args: Any, **kwargs: Any) -> Any:
            if not session.get("user_id"):
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login", next=request.path))
            return view_func(*args, **kwargs)

        return wrapped_view

    def admin_required(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapped_view(*args: Any, **kwargs: Any) -> Any:
            user = get_current_user()
            if not user or not user.is_admin:
                flash("Administrator access required.", "danger")
                return redirect(url_for("index"))
            return view_func(*args, **kwargs)

        return wrapped_view

    @app.context_processor
    def inject_context() -> dict[str, Any]:
        user = get_current_user()
        return {
            "current_user": user,
            "get_pet_image": get_pet_image,
        }

    # ---------------- Routes: Public & Catalog ---------------- #
    @app.route("/")
    def index():
        try:
            metrics = adoption_service.get_adoption_metrics()
        except Exception:
            metrics = {
                "total_pets": 0,
                "available_pets": 0,
                "pending_pets": 0,
                "adopted_pets": 0,
                "pending_apps": 0,
                "total_users": 0,
                "species_breakdown": [],
            }

        # Featured pets (up to 6 available)
        featured = pet_service.list_pets(status="available")[:6]
        species_list = pet_service.get_species_list()

        return render_template(
            "index.html",
            metrics=metrics,
            featured_pets=featured,
            species_list=species_list,
        )

    @app.route("/pets")
    def pets_catalog():
        species = request.args.get("species", "").strip() or None
        status = request.args.get("status", "").strip() or None
        search = request.args.get("search", "").strip() or None
        order_by = request.args.get("order_by", "id ASC").strip()

        pets = pet_service.list_pets(
            status=status,
            species=species,
            search=search,
            order_by=order_by,
        )
        species_list = pet_service.get_species_list()

        return render_template(
            "pets.html",
            pets=pets,
            species_list=species_list,
            selected_species=species or "",
            selected_status=status or "",
            selected_order=order_by,
            search_query=search or "",
        )

    @app.route("/pets/<int:pet_id>")
    def pet_detail(pet_id: int):
        pet = pet_service.get_pet_by_id(pet_id)
        if not pet:
            flash(f"Pet #{pet_id} not found.", "warning")
            return redirect(url_for("pets_catalog"))

        # Check if user already submitted application
        has_pending_app = False
        user = get_current_user()
        if user:
            apps = adoption_service.get_user_applications(user.id)
            has_pending_app = any(a.pet_id == pet_id and a.status == "pending" for a in apps)

        return render_template(
            "pet_detail.html",
            pet=pet,
            has_pending_app=has_pending_app,
        )

    # ---------------- Routes: Adoption Application ---------------- #
    @app.route("/apply/<int:pet_id>", methods=["GET", "POST"])
    @login_required
    def apply_adoption(pet_id: int):
        pet = pet_service.get_pet_by_id(pet_id)
        if not pet:
            flash("Pet not found.", "danger")
            return redirect(url_for("pets_catalog"))

        if pet.status.lower() == "adopted":
            flash("This pet has already been lovingly adopted!", "info")
            return redirect(url_for("pet_detail", pet_id=pet_id))

        user = get_current_user()

        if request.method == "POST":
            applicant_name = request.form.get("applicant_name", "").strip() or user.full_name
            applicant_phone = request.form.get("applicant_phone", "").strip() or user.phone
            applicant_email = request.form.get("applicant_email", "").strip() or user.email
            living_space = request.form.get("living_space", "House")
            has_other_pets = request.form.get("has_other_pets") == "yes"
            experience_notes = request.form.get("experience_notes", "").strip()

            success, message, app_id = adoption_service.submit_application(
                pet_id=pet_id,
                user_id=user.id,
                applicant_name=applicant_name,
                applicant_phone=applicant_phone,
                applicant_email=applicant_email,
                living_space=living_space,
                has_other_pets=has_other_pets,
                experience_notes=experience_notes,
            )

            if success:
                flash(message, "success")
                return redirect(url_for("my_applications"))
            else:
                flash(message, "danger")

        return render_template("apply.html", pet=pet, user=user)

    @app.route("/my-applications")
    @login_required
    def my_applications():
        user = get_current_user()
        applications = adoption_service.get_user_applications(user.id)
        return render_template("my_applications.html", applications=applications)

    @app.route("/applications/<int:app_id>/withdraw", methods=["POST"])
    @login_required
    def withdraw_application(app_id: int):
        user = get_current_user()
        app_record = adoption_service.get_application_by_id(app_id)
        if not app_record or app_record.user_id != user.id:
            flash("Application not found or unauthorized.", "danger")
            return redirect(url_for("my_applications"))

        if app_record.status.lower() != "pending":
            flash("Only pending applications can be withdrawn.", "warning")
            return redirect(url_for("my_applications"))

        success, msg = adoption_service.review_application(
            app_id=app_id,
            new_status="withdrawn",
            reviewer_notes="Withdrawn by applicant.",
        )
        if success:
            flash("Your application has been withdrawn.", "info")
        else:
            flash(msg, "danger")
        return redirect(url_for("my_applications"))

    # ---------------- Routes: Authentication ---------------- #
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, username, password_hash, salt, role, full_name, email, phone, created_at
                        FROM users
                        WHERE LOWER(username) = LOWER(%s);
                        """,
                        (username,),
                    )
                    row = cur.fetchone()

                    if row and verify_password(password, row["password_hash"], row["salt"]):
                        session["user_id"] = row["id"]
                        session["username"] = row["username"]
                        session["role"] = row["role"]
                        session["full_name"] = row["full_name"]
                        flash(f"Welcome back, {row['full_name']}!", "success")
                        next_url = request.args.get("next")
                        if next_url and next_url.startswith("/"):
                            return redirect(next_url)
                        if row["role"].lower() == "admin":
                            return redirect(url_for("admin_dashboard"))
                        return redirect(url_for("index"))
                    else:
                        flash("Invalid username or password.", "danger")

        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if session.get("user_id"):
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()

            if not username or not password or not full_name or not email:
                flash("Please fill in all required fields.", "warning")
                return render_template("register.html")

            if password != confirm_password:
                flash("Passwords do not match.", "warning")
                return render_template("register.html")

            pwd_hash, salt = hash_password(password)

            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO users (username, password_hash, salt, role, full_name, email, phone)
                            VALUES (%s, %s, %s, 'adopter', %s, %s, %s)
                            RETURNING id, username, role, full_name;
                            """,
                            (username, pwd_hash, salt, full_name, email, phone),
                        )
                        new_user = cur.fetchone()
                        conn.commit()

                        session["user_id"] = new_user["id"]
                        session["username"] = new_user["username"]
                        session["role"] = new_user["role"]
                        session["full_name"] = new_user["full_name"]
                        flash("Account created successfully! Welcome to PawHaven.", "success")
                        return redirect(url_for("index"))
            except Exception as exc:
                err_msg = str(exc)
                if "users_username_key" in err_msg:
                    flash("That username is already taken.", "danger")
                elif "users_email_key" in err_msg:
                    flash("That email address is already registered.", "danger")
                else:
                    flash(f"Registration failed: {err_msg}", "danger")

        return render_template("register.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        user = get_current_user()
        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()

            success, msg = user_service.update_profile(user.id, full_name, email, phone)
            if success:
                flash("Profile updated successfully.", "success")
                session["full_name"] = full_name
                user = get_current_user()
            else:
                flash(msg, "danger")

        return render_template("profile.html", user=user)

    # ---------------- Routes: Shelter Admin ---------------- #
    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        metrics = adoption_service.get_adoption_metrics()
        status_filter = request.args.get("app_status")
        applications = adoption_service.get_all_applications(status=status_filter)
        pets = pet_service.list_pets(order_by="id DESC")
        users = user_service.list_users()

        return render_template(
            "admin.html",
            metrics=metrics,
            applications=applications,
            pets=pets,
            users=users,
            current_app_status=status_filter or "all",
        )

    @app.route("/admin/pets/add", methods=["POST"])
    @admin_required
    def admin_add_pet():
        name = request.form.get("name", "").strip()
        species = request.form.get("species", "").strip()
        breed = request.form.get("breed", "").strip()
        age_years = float(request.form.get("age_years", 1.0))
        gender = request.form.get("gender", "Unknown")
        size = request.form.get("size", "Medium")
        fee = Decimal(request.form.get("fee", "0"))
        description = request.form.get("description", "").strip()
        health_status = request.form.get("health_status", "Healthy")
        vaccinated = request.form.get("vaccinated") == "on"
        spayed_neutered = request.form.get("spayed_neutered") == "on"

        try:
            pet_service.add_pet(
                name=name,
                species=species,
                breed=breed,
                age_years=age_years,
                gender=gender,
                size=size,
                fee=fee,
                description=description,
                health_status=health_status,
                vaccinated=vaccinated,
                spayed_neutered=spayed_neutered,
            )
            flash(f"Pet '{name}' added successfully to adoption catalog!", "success")
        except Exception as exc:
            flash(f"Failed to add pet: {exc}", "danger")

        return redirect(url_for("admin_dashboard") + "#pets-tab")

    @app.route("/admin/pets/<int:pet_id>/status", methods=["POST"])
    @admin_required
    def admin_change_pet_status(pet_id: int):
        new_status = request.form.get("status", "available").strip().lower()
        if pet_service.update_pet_status(pet_id, new_status):
            flash(f"Pet #{pet_id} status updated to {new_status.upper()}.", "success")
        else:
            flash("Could not update pet status.", "danger")
        return redirect(url_for("admin_dashboard") + "#pets-tab")

    @app.route("/admin/pets/<int:pet_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_pet(pet_id: int):
        if pet_service.delete_pet(pet_id):
            flash(f"Pet #{pet_id} was removed from the system.", "info")
        else:
            flash("Failed to delete pet.", "danger")
        return redirect(url_for("admin_dashboard") + "#pets-tab")

    @app.route("/admin/applications/<int:app_id>/review", methods=["POST"])
    @admin_required
    def admin_review_application(app_id: int):
        decision = request.form.get("decision", "").strip().lower()
        notes = request.form.get("reviewer_notes", "").strip()

        success, msg = adoption_service.review_application(app_id, decision, notes)
        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("admin_dashboard") + "#applications-tab")

    # ---------------- Routes: DBMS Academic Suite ---------------- #
    @app.route("/dbms")
    def dbms_suite():
        schema_text = dbms_service.get_relational_schema_overview()
        prebuilt = dbms_service.get_prebuilt_queries()
        stats = dbms_service.get_database_catalog_stats()
        audit_logs = dbms_service.get_audit_trail()

        return render_template(
            "dbms.html",
            schema_text=schema_text,
            prebuilt_queries=prebuilt,
            catalog_stats=stats,
            audit_logs=audit_logs,
        )

    @app.route("/api/dbms/execute", methods=["POST"])
    def api_dbms_execute():
        data = request.get_json(force=True) or {}
        sql = data.get("sql", "").strip()
        explain = data.get("explain", False)

        if not sql:
            return jsonify({"success": False, "error": "Query cannot be empty."}), 400

        if explain:
            success, lines, err = dbms_service.explain_query_plan(sql)
            return jsonify({"success": success, "plan": lines, "error": err})

        success, columns, rows, elapsed, error = dbms_service.execute_arbitrary_query(sql)
        # Format rows for JSON serialization
        json_rows = []
        for r in rows:
            json_rows.append([str(c) if c is not None else "NULL" for c in r])

        return jsonify({
            "success": success,
            "columns": columns,
            "rows": json_rows,
            "row_count": len(rows),
            "execution_ms": elapsed,
            "error": error,
        })

    @app.route("/api/dbms/acid-test", methods=["POST"])
    def api_dbms_acid_test():
        data = request.get_json(silent=True) or {}
        simulate_failure = data.get("simulate_failure", False)
        result = dbms_service.demonstrate_acid_transaction(simulate_failure=simulate_failure)
        return jsonify(result)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
