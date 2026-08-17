"""HTTP routes for Import and Export functionalities across HMS modules."""
import os
import tempfile
import typing
from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from app.auth.utils import role_required
from app.services.import_export_service import ImportExportService

import_export_bp = Blueprint("import_export", __name__, url_prefix="/data")


@import_export_bp.route("/")
@import_export_bp.route("/hub")
@login_required
def hub() -> typing.Any:
    """Render the central Data Management Hub for all modules."""
    modules = ImportExportService.list_supported_modules()
    return render_template(
        "modules/import_export/hub.html",
        modules=modules,
    )


@import_export_bp.route("/<module_name>/template")
@login_required
def download_template(module_name: str) -> typing.Any:
    """Download a starter CSV template with column headers and a sample row.

    Args:
        module_name: Lowercase module name.

    Returns:
        CSV file response attachment.
    """
    try:
        csv_content: str = ImportExportService.generate_template_csv(module_name)
        filename: str = f"{module_name}_template.csv"
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as err:
        flash(str(err), "danger")
        return redirect(url_for("import_export.hub"))


@import_export_bp.route("/<module_name>/export")
@login_required
def export_data(module_name: str) -> typing.Any:
    """Export records from a module to CSV or JSON format and download the file.

    Args:
        module_name: Lowercase module name.

    Returns:
        File attachment stream for download.
    """
    export_format: str = request.args.get("format", "csv").lower()
    search_query: str = request.args.get("search", "")

    try:
        file_path, download_filename, count = ImportExportService.export_data(
            module_name=module_name,
            export_format=export_format,
            search_query=search_query,
        )

        if not os.path.exists(file_path):
            flash("Failed to generate export file.", "danger")
            return redirect(request.referrer or url_for("main.dashboard"))

        mimetype = "text/csv" if export_format == "csv" else "application/json"
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_filename,
        )
    except Exception as err:
        flash(f"Export failed: {err}", "danger")
        return redirect(request.referrer or url_for("main.dashboard"))


@import_export_bp.route("/<module_name>/import", methods=["GET"])
@login_required
def import_page(module_name: str) -> typing.Any:
    """Render the interactive import page for a module.

    Args:
        module_name: Lowercase module name.

    Returns:
        Rendered HTML import interface.
    """
    config = ImportExportService.get_module_config(module_name)
    if config is None:
        flash(f"Module '{module_name}' is not recognized.", "danger")
        return redirect(url_for("import_export.hub"))

    return render_template(
        "modules/import_export/import.html",
        config=config,
        module_name=module_name,
    )


@import_export_bp.route("/<module_name>/validate", methods=["POST"])
@login_required
def validate_import_file(module_name: str) -> typing.Any:
    """AJAX endpoint: dry-run validate an uploaded import file and return row preview.

    Args:
        module_name: Lowercase module name.

    Returns:
        JSON object with preview records, headers count, and validation status.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"success": False, "message": "Please select a valid file."}), 400

    export_format: str = request.form.get("format", "csv").lower()
    filename_lower: str = uploaded_file.filename.lower()
    if filename_lower.endswith(".json"):
        export_format = "json"
    elif filename_lower.endswith(".csv"):
        export_format = "csv"

    temp_dir = tempfile.gettempdir()
    temp_suffix = ".json" if export_format == "json" else ".csv"
    with tempfile.NamedTemporaryFile(
        dir=temp_dir, suffix=temp_suffix, delete=False
    ) as temp_file:
        uploaded_file.save(temp_file.name)
        temp_file_path = temp_file.name

    try:
        validation_result: dict[str, typing.Any] = (
            ImportExportService.preview_and_validate(
                module_name=module_name,
                file_path=temp_file_path,
                export_format=export_format,
            )
        )
        return jsonify(validation_result)
    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


@import_export_bp.route("/<module_name>/import", methods=["POST"])
@login_required
def execute_import(module_name: str) -> typing.Any:
    """Execute record import from uploaded CSV/JSON file with optional upsert.

    Args:
        module_name: Lowercase module name.

    Returns:
        Redirect with flash notification or JSON response for AJAX requests.
    """
    if "file" not in request.files:
        flash("No file was uploaded.", "danger")
        return redirect(url_for("import_export.import_page", module_name=module_name))

    uploaded_file = request.files["file"]
    if not uploaded_file or not uploaded_file.filename:
        flash("Please choose a valid CSV or JSON file.", "danger")
        return redirect(url_for("import_export.import_page", module_name=module_name))

    export_format: str = request.form.get("format", "csv").lower()
    filename_lower: str = uploaded_file.filename.lower()
    if filename_lower.endswith(".json"):
        export_format = "json"
    elif filename_lower.endswith(".csv"):
        export_format = "csv"

    upsert_field: str = request.form.get("upsert_on", "").strip()
    upsert_on: list[str] = [upsert_field] if upsert_field else []

    temp_dir = tempfile.gettempdir()
    temp_suffix = ".json" if export_format == "json" else ".csv"
    with tempfile.NamedTemporaryFile(
        dir=temp_dir, suffix=temp_suffix, delete=False
    ) as temp_file:
        uploaded_file.save(temp_file.name)
        temp_file_path = temp_file.name

    try:
        import_result: dict[str, typing.Any] = ImportExportService.execute_import(
            module_name=module_name,
            file_path=temp_file_path,
            export_format=export_format,
            upsert_on=upsert_on,
        )

        succeeded = import_result.get("succeeded_records", 0)
        failed = import_result.get("failed_records", 0)
        total = import_result.get("total_records", 0)

        if succeeded > 0 and failed == 0:
            flash(
                f"Successfully imported all {succeeded} record(s) into {module_name.title()}!",
                "success",
            )
        elif succeeded > 0 and failed > 0:
            flash(
                f"Import completed with warnings: {succeeded} of {total} record(s) imported. {failed} record(s) failed.",
                "warning",
            )
        else:
            flash(
                f"Import failed: {import_result.get('message', 'No records were imported.')}",
                "danger",
            )

        # Redirect to the module's primary list view
        target_endpoint = f"{module_name}.{module_name}_list"
        return redirect(url_for(target_endpoint))
    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
