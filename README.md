# App Version Control System

## Project Overview

This project is an application management system that allows users to monitor, update, and launch applications from a central interface. It consists of two main components:

1. **App Control Client**: A PyQt5-based desktop application for managing applications.
2. **Server**: A Flask backend that handles version tracking and file distribution.

## Key Features

- **Application Management**: View, update, and launch applications.
- **Version Control**: Automatically detect and update applications to their latest versions.
- **File Encryption**: Securely store applications using encryption.
- **Error Logging**: Comprehensive error tracking and log management.
- **Server Connection Monitoring**: Real-time server connectivity status.

## Technical Architecture

### Client Application (`app_control.py`)

The client application provides a modern user interface with the following components:

- **Sidebar Navigation**: Access different sections of the application.
- **Application Cards**: Visual representation of each managed application.
- **Server Connection Indicator**: Real-time server connection status.
- **Error Logs Viewer**: View and manage application errors.

### Server (`app.py`)

The server provides endpoints for:

- Retrieving application configuration.
- Getting the latest version information.
- Downloading application executables and assets.

### Updater Module (`updater.py`)

Handles version comparison and application updating logic:

- `get_local_version()`: Detects installed application versions.
- `get_remote_version()`: Retrieves the latest version information from the server.
- `download_new_version()`: Downloads and installs application updates.

## Data Flow

1. **Application Startup**:

   - The client connects to the server to fetch application configuration.
   - Local versions are compared with server versions.
   - The UI updates to indicate available updates or ready-to-launch status.

2. **Update Process**:

   - The user initiates an update for an application.
   - The client downloads the latest version from the server.
   - Progress is displayed via a progress bar.
   - The application is encrypted and stored locally.

3. **Launch Process**:

   - The user initiates application launch.
   - The client decrypts the application to a temporary location.
   - The application is executed as a subprocess.
   - Temporary files are cleaned up after execution.

4. **Error Logging**:
   - Errors are captured and stored in `error_log.json`.
   - Logs are displayed in the UI grouped by date.
   - Users can clear logs or copy error details.

## Security Features

- **File Encryption**: Applications are encrypted using Fernet symmetric encryption.
- **Key Derivation**: PBKDF2HMAC with SHA-256 is used for key generation.
- **Temporary Execution**: Applications are decrypted to temporary locations for execution.

## Directory Structure

```
├── app_control/
│   ├── app_control.py     # Main client application
│   ├── updater.py         # Version management and update logic
│   ├── apps/              # Encrypted application storage
│   ├── assets/            # Application icons and assets
│   └── logs/              # Error logs storage
├── server/
│   ├── app.py             # Flask server application
│   ├── data/              # Application configuration and version info
│   ├── static/            # Application files for distribution
│   └── assets/            # Icon files for distribution
```

## Usage

1. Start the server:

   ```bash
   cd server
   python app.py
   ```

2. Launch the client:

   ```bash
   cd app_control
   python app_control.py
   ```

3. Use the interface to manage your applications:
   - Update applications when new versions are available.
   - Launch applications with a single click.
   - Monitor and manage error logs.

## Dependencies

- Python 3.6+
- PyQt5
- Flask
- Requests
- Cryptography

## Conclusion

This application provides a robust solution for managing application versions and updates in a secure and user-friendly manner. The combination of a modern UI, secure file handling, and comprehensive error logging creates a complete application management ecosystem.
