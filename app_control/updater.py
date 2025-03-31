import os
import requests
from tqdm import tqdm
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Replace with your server's address if different
SERVER_URL = "http://127.0.0.1:5000"

def get_local_version(apps_folder, executable_prefix):
    """
    Check the local version of the app by scanning for executables with the given prefix.
    Returns a tuple of (version_tuple, filename) or (None, None) if not found.
    """
    files = [f for f in os.listdir(apps_folder) if f.startswith(executable_prefix) and f.endswith(".exe")]
    if not files:
        return None, None

    def parse_version(filename):
        # Extract version from filename, e.g., "WorkForce_00.01.exe"
        version_str = filename.replace(executable_prefix, "").replace(".exe", "")
        major, minor = version_str.split(".")
        return (int(major), int(minor)), filename

    versions = [parse_version(f) for f in files]
    versions.sort()  # Sorts by version tuple
    return versions[-1]  # Return the highest version

def get_remote_version(app_name):
    """
    Fetch the latest version information from the server for the given app.
    Returns a tuple of (version_tuple, version_str).
    """
    response = requests.get(f"{SERVER_URL}/latest-version/{app_name}")
    response.raise_for_status()
    latest_version = response.json()["latest_version"]
    major, minor = latest_version.split(".")
    return (int(major), int(minor)), latest_version

def generate_key(password, salt):
    """
    Generate an encryption key from a password and salt using PBKDF2HMAC.
    """
    kdf = PBKDF2HMAC(
         algorithm=hashes.SHA256(),
         length=32,
         salt=salt,
         iterations=100000,
         backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

def encrypt_file(input_file, output_file, key):
    """
    Encrypt the file at input_file using Fernet encryption and save to output_file.
    """
    fernet = Fernet(key)
    with open(input_file, "rb") as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(output_file, "wb") as f:
        f.write(encrypted)

def download_new_version(apps_folder, executable_prefix, version_str, progress_callback=None):
    """
    Download the latest app executable from the server, encrypt it, and save it locally.

    Args:
        apps_folder (str): The local folder to save the executable.
        executable_prefix (str): The prefix for the app's executable filename.
        version_str (str): The version string (e.g., "00.01").
        progress_callback (function, optional): A callback that takes (current, total) bytes.

    Returns:
        str: The filename of the downloaded and encrypted executable.
    """
    filename = f"{executable_prefix}{version_str}.exe"
    url = f"{SERVER_URL}/download/{filename}"
    temp_filepath = os.path.join(apps_folder, f"temp_{filename}")
    final_filepath = os.path.join(apps_folder, filename)

    print(f"Downloading {filename} from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get("content-length", 0))
    with open(temp_filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                if progress_callback:
                    progress_callback(f.tell(), total_size)
    print(f"Downloaded {filename}. Now encrypting...")

    # Use a constant salt and password for demonstration purposes.
    # In production, consider more secure key management practices.
    salt = b"app_control_salt"
    password = b"this_is_a_secret_password_for_app_control"
    key = generate_key(password, salt)
    encrypt_file(temp_filepath, final_filepath, key)
    os.remove(temp_filepath)
    print(f"Encrypted {filename} to {final_filepath}")
    return filename

def check_for_updates(apps_folder, executable_prefix, app_name):
    """
    Check if the app needs an update by comparing the local and remote versions.
    If an update is required, download the new version.

    Args:
        apps_folder (str): The folder where executables are stored.
        executable_prefix (str): The prefix for the app's executable filename.
        app_name (str): The name of the app.

    Returns:
        str: The filename of the updated executable.
    """
    local_version, local_filename = get_local_version(apps_folder, executable_prefix)
    print(f"Local version for {app_name}: {local_version if local_version else 'None'}")
    remote_version, remote_str = get_remote_version(app_name)
    print(f"Remote version for {app_name}: {remote_version}")
    if local_version is None or remote_version > local_version:
        print("Updating to the latest version...")
        new_filename = download_new_version(apps_folder, executable_prefix, remote_str)
        if local_filename and local_filename != new_filename:
            os.remove(os.path.join(apps_folder, local_filename))
        return new_filename
    else:
        print("No updates needed.")
        return local_filename

if __name__ == "__main__":
    # For testing purposes, create a local 'apps' folder and run version checks.
    test_apps_folder = "apps"
    os.makedirs(test_apps_folder, exist_ok=True)
    
    app_name = "WorkForce"
    executable_prefix = "WorkForce_"
    
    # Check and print the local version.
    local_version, local_filename = get_local_version(test_apps_folder, executable_prefix)
    print("Local version:", local_version)
    
    # Fetch and print the remote version.
    remote_version, remote_str = get_remote_version(app_name)
    print("Remote version:", remote_version)
    
    # Optionally, trigger an update if needed.
    updated_filename = check_for_updates(test_apps_folder, executable_prefix, app_name)
    print("Updated executable filename:", updated_filename)
