import os
import requests
from tqdm import tqdm

SERVER_URL = "http://127.0.0.1:5000"  # Replace with your server's address


def get_local_version(apps_folder, executable_prefix):
    """
    Check the local version of the app by scanning for executables with the given prefix.
    """
    files = [
        f for f in os.listdir(apps_folder) if f.startswith(executable_prefix) and f.endswith(".exe")
    ]
    if not files:
        return None, None

    def parse_version(filename):
        version_str = filename.replace(executable_prefix, "").replace(".exe", "")
        major, minor = version_str.split(".")
        return (int(major), int(minor)), filename

    versions = [parse_version(f) for f in files]
    versions.sort()
    return versions[-1]  # Return the highest version


def get_remote_version(app_name):
    """
    Fetch the latest version information from the server for the given app.
    """
    response = requests.get(f"{SERVER_URL}/latest-version/{app_name}")
    response.raise_for_status()
    latest_version = response.json()["latest_version"]
    major, minor = latest_version.split(".")
    return (int(major), int(minor)), latest_version


def download_new_version(apps_folder, executable_prefix, version_str, progress_callback=None):
    """
    Download the latest app executable from the server with progress updates.
    """
    filename = f"{executable_prefix}{version_str}.exe"
    url = f"{SERVER_URL}/download/{filename}"
    filepath = os.path.join(apps_folder, filename)

    print(f"Downloading {filename}...")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
            if progress_callback:
                progress_callback(f.tell(), total_size)

    print(f"Downloaded {filename} to {filepath}")
    return filename

def check_for_updates(workforce_folder):
    """
    Compare the local and remote versions, and update if necessary.
    """
    # Get local version
    local_version, local_filename = get_local_version(workforce_folder)
    print(f"Local version: {local_version if local_version else 'None'}")

    # Get remote version
    remote_version, remote_str = get_remote_version()
    print(f"Remote version: {remote_version}")

    # Compare versions
    if local_version is None or remote_version > local_version:
        print("Updating to the latest version...")
        new_filename = download_new_version(workforce_folder, remote_str)

        # Remove old version if applicable
        if local_filename and local_filename != new_filename:
            os.remove(os.path.join(workforce_folder, local_filename))
        return new_filename
    else:
        print("No updates needed.")
        return local_filename
