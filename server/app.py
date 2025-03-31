from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

# Path to the directory where executables and metadata are stored
STATIC_DIR = os.path.join(os.getcwd(), "static")
DATA_DIR = os.path.join(os.getcwd(), "data")


@app.route('/latest-version/<app_name>', methods=['GET'])
def latest_version(app_name):
    """
    Serve the latest version information for the given app.
    """
    version_file = os.path.join(DATA_DIR, f'{app_name}_version.txt')
    if not os.path.exists(version_file):
        return jsonify({'error': 'Version file not found'}), 404

    with open(version_file, 'r') as f:
        latest_version = f.read().strip()
    return jsonify({'latest_version': latest_version})


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Serve the requested executable file.
    """
    if not os.path.exists(os.path.join(STATIC_DIR, filename)):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(STATIC_DIR, filename)


if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # Run the server
    app.run(host='0.0.0.0', port=5000)
