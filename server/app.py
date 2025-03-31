from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

# Directories for executables, version info, and assets (icons)
STATIC_DIR = os.path.join(os.getcwd(), "static")
DATA_DIR = os.path.join(os.getcwd(), "data")
ASSETS_DIR = os.path.join(os.getcwd(), "assets")

# Ensure required directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)


@app.route("/latest-version/<app_name>", methods=["GET"])
def latest_version(app_name):
    """
    Return the latest version info for an app.
    """
    version_file = os.path.join(DATA_DIR, f"{app_name}_version.txt")
    if not os.path.exists(version_file):
        return jsonify({"error": f"Version info for {app_name} not found"}), 404

    with open(version_file, "r") as f:
        version_str = f.read().strip()

    try:
        version_parts = version_str.split(".")
        version_num = float(f"{version_parts[0]}.{version_parts[1]}")
        return jsonify({"version": version_num, "version_string": version_str})
    except Exception as e:
        return jsonify({"error": f"Invalid version format: {str(e)}"}), 500


@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """
    Serve an executable file for download.
    """
    if not os.path.exists(os.path.join(STATIC_DIR, filename)):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(STATIC_DIR, filename)


@app.route("/apps", methods=["GET"])
def list_apps():
    """
    Return the apps configuration as a JSON list.
    """
    apps = [
        {
            "name": "WorkForce",
            "executable_prefix": "WorkForce_",
            "icon": "workforce_icon.png",
        },
        {
            "name": "PersonnelManagement",
            "executable_prefix": "PersonnelManagement_",
            "icon": "personnel_icon.png",
        },
    ]
    return jsonify({"apps": apps})


@app.route("/assets/<path:filename>", methods=["GET"])
def download_asset(filename):
    """
    Serve an asset (icon) file.
    """
    if not os.path.exists(os.path.join(ASSETS_DIR, filename)):
        return jsonify({"error": "Asset not found"}), 404
    return send_from_directory(ASSETS_DIR, filename)


@app.route("/", methods=["GET"])
def index():
    """
    Root endpoint for server health checks
    """
    return jsonify({"status": "ok", "message": "App Version Control Server is running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
