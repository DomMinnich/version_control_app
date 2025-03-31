from flask import Flask, send_from_directory, jsonify
import os
import json

app = Flask(__name__)

# Directories for executables, version info, and assets (icons)
STATIC_DIR = os.path.join(os.getcwd(), "static")
DATA_DIR = os.path.join(os.getcwd(), "data")
ASSETS_DIR = os.path.join(os.getcwd(), "assets")

# Ensure required directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(DATA_DIR, "apps_config.json")


# Helper function to load app configuration
def load_app_config():
    if not os.path.exists(CONFIG_FILE):
        # Create default config file if it doesn't exist
        default_config = {
            "apps": [
                {
                    "name": "WorkForce",
                    "executable_prefix": "WorkForce_",
                    "icon": "workforce_icon.png",
                    "version": "00.01",
                },
                {
                    "name": "PersonnelManagement",
                    "executable_prefix": "PersonnelManagement_",
                    "icon": "personnel_icon.png",
                    "version": "00.01",
                },
            ]
        }
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=2)

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


@app.route("/latest-version/<app_name>", methods=["GET"])
def latest_version(app_name):
    """
    Return the latest version info for an app.
    """
    config = load_app_config()
    app_info = next((app for app in config["apps"] if app["name"] == app_name), None)
    if not app_info:
        return jsonify({"error": f"App {app_name} not found"}), 404

    version_str = app_info["version"]
    try:
        version_parts = version_str.split(".")
        version_num = float(f"{version_parts[0]}.{version_parts[1]}")
        # Include "latest_version" key to match client expectations
        return jsonify(
            {
                "version": version_num,
                "version_string": version_str,
                "latest_version": version_str,
            }
        )
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
    config = load_app_config()
    return jsonify({"apps": config["apps"]})


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
