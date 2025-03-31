import os
import sys
import json
import datetime
import subprocess
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PyQt5.QtCore import Qt, QPropertyAnimation, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QFont, QIcon, QCursor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QWidget, QProgressBar,
    QFrame, QStackedWidget, QScrollArea, QSizePolicy
)
from updater import get_local_version, get_remote_version, download_new_version

APPS_FOLDER = os.path.join(os.getcwd(), "apps")
LOGS_FOLDER = os.path.join(os.getcwd(), "logs")
ERROR_LOG_FILE = os.path.join(LOGS_FOLDER, "error_log.json")

APPS_CONFIG = [
    {
        "name": "WorkForce",
        "executable_prefix": "WorkForce_",
        "icon": "assets/workforce_icon.png",
    },
    {
        "name": "PersonnelManagement",
        "executable_prefix": "PersonnelManagement_",
        "icon": "assets/personnel_icon.png",
    },
]


class AppControl(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window properties
        self.setWindowTitle("App Version Control")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #23263A;")

        # Create logs directory if it doesn't exist
        os.makedirs(LOGS_FOLDER, exist_ok=True)

        # Initialize error log if it doesn't exist
        if not os.path.exists(ERROR_LOG_FILE):
            with open(ERROR_LOG_FILE, "w") as f:
                json.dump([], f)

        # Main layout
        self.central_layout = QHBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self.central_layout)
        self.setCentralWidget(central_widget)

        # Sidebar
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setSpacing(20)
        self.sidebar_layout.setAlignment(Qt.AlignTop)
        self.create_sidebar()

        sidebar_container = QFrame()
        sidebar_container.setLayout(self.sidebar_layout)
        sidebar_container.setStyleSheet(
            """
            QFrame {
                background-color: #1E202D;
                border-right: 2px solid #2A2D45;
                padding: 10px;
            }
        """
        )
        self.central_layout.addWidget(sidebar_container, 0)

        # Content Area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet(
            "background-color: #2A2D45; border-radius: 15px;"
        )
        self.central_layout.addWidget(self.content_area, 1)

        # Add pages to content area
        self.create_home_page()
        self.create_error_logs_page()
        self.create_about_page()
        self.create_settings_page()

    def create_sidebar(self):
        """
        Create a sidebar with navigation options.
        """
        # App logo or icon
        logo = QLabel()
        logo.setPixmap(QPixmap("assets/logo.png").scaled(100, 100, Qt.KeepAspectRatio))
        logo.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(logo)

        # Sidebar buttons
        self.create_sidebar_button("Home", self.show_home_page)
        self.create_sidebar_button("Error Logs", self.show_error_logs_page)
        self.create_sidebar_button("About", self.show_about_page)
        self.create_sidebar_button("Settings", self.show_settings_page)
        self.create_sidebar_button("Exit", self.exit_application)

    def create_sidebar_button(self, name, action):
        """
        Create a sidebar button.
        """
        btn = QPushButton(name)
        btn.setFont(QFont("Arial", 14))
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2A2D45;
                color: #FFFFFF;
                border-radius: 10px;
                padding: 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #44475A;
            }
        """
        )
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(action)
        self.sidebar_layout.addWidget(btn)

    def create_home_page(self):
        """
        Create the Home page for managing apps.
        """
        home_page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header = QLabel("App Management")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.app_widgets = {}
        for app in APPS_CONFIG:
            layout.addWidget(self.create_app_card(app))

        self.add_footer(layout)
        home_page.setLayout(layout)
        self.content_area.addWidget(home_page)

    def create_about_page(self):
        """
        Create the About page.
        """
        about_page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("About App Control")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)

        description = QLabel(
            "App Control is a tool to manage and update your applications seamlessly."
        )
        description.setFont(QFont("Arial", 16))
        description.setStyleSheet("color: #CCCCCC;")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)

        self.add_footer(layout)
        about_page.setLayout(layout)
        self.content_area.addWidget(about_page)

    def create_settings_page(self):
        """
        Create the Settings page.
        """
        settings_page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Settings")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)

        placeholder = QLabel("Settings options go here...")
        placeholder.setFont(QFont("Arial", 16))
        placeholder.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(placeholder)

        self.add_footer(layout)
        settings_page.setLayout(layout)
        self.content_area.addWidget(settings_page)

    def create_error_logs_page(self):
        """
        Create the Error Logs page to view application errors.
        """
        error_page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # Header
        header = QLabel("Error Logs")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Scrollable area for logs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2A2D45;
                width: 15px;
                margin: 15px 3px 15px 3px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #44475A;
                min-height: 30px;
                border-radius: 4px;
            }
        """
        )

        # Container for logs
        self.logs_container = QWidget()
        self.logs_layout = QVBoxLayout(self.logs_container)
        self.logs_layout.setAlignment(Qt.AlignTop)
        self.logs_layout.setSpacing(10)

        # Load and display logs
        self.load_error_logs()

        scroll_area.setWidget(self.logs_container)
        layout.addWidget(scroll_area)

        # Button to clear logs
        clear_logs_btn = QPushButton("Clear All Logs")
        clear_logs_btn.setFont(QFont("Arial", 12))
        clear_logs_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF5555;
                color: #FFFFFF;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #FF6E6E;
            }
        """
        )
        clear_logs_btn.clicked.connect(self.clear_error_logs)
        clear_logs_btn.setCursor(Qt.PointingHandCursor)

        # Center the button
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_logs_btn)
        btn_layout.addStretch()
        layout.addWidget(btn_container)

        self.add_footer(layout)
        error_page.setLayout(layout)
        self.content_area.addWidget(error_page)

    def add_footer(self, layout):
        """
        Add a footer to the given layout.
        """
        footer = QLabel("Developed by Dominic Minnich")
        footer.setFont(QFont("Arial", 10))
        footer.setStyleSheet("color: #CCCCCC; margin-top: 20px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    def create_app_card(self, app_config):
        """
        Create a card for an individual app.
        """
        app_name = app_config["name"]
        executable_prefix = app_config["executable_prefix"]
        icon_path = app_config.get("icon", "")

        # Card container
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background-color: #2F344B;
                border-radius: 15px;
                padding: 20px;
            }
        """
        )
        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setAlignment(Qt.AlignLeft)  # Align left for proper icon positioning

        # App Icon - positioned at the left
        if os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(
                QPixmap(icon_path).scaled(100, 100, Qt.KeepAspectRatio)
            )
            icon_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            card_layout.addWidget(icon_label)

        # Spacer to push content to center
        card_layout.addStretch(1)

        # App Info and Buttons - in the center
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)  # Center the contents vertically

        # App Name Label
        app_label = QLabel(app_name)
        app_label.setFont(QFont("Arial", 18, QFont.Bold))
        app_label.setStyleSheet("color: #FFFFFF;")
        app_label.setAlignment(Qt.AlignCenter)  # Center the text
        info_layout.addWidget(app_label)

        # Progress Bar
        progress_bar = QProgressBar()
        progress_bar.setTextVisible(False)
        progress_bar.setFixedWidth(300)  # Fixed width for consistency
        progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #2A2D45;
                border-radius: 5px;
                background-color: #44475A;
            }
            QProgressBar::chunk {
                background-color: #50FA7B;
            }
        """
        )
        progress_bar.setVisible(False)
        progress_bar.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(
            progress_bar, 0, Qt.AlignCenter
        )  # Center the progress bar

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)  # Center the buttons horizontally

        update_button = self.create_animated_button(
            f"Update {app_name}", "#FF5555", "#FF6E6E"
        )
        update_button.clicked.connect(
            lambda: self.update_app(
                app_name, executable_prefix, app_label, progress_bar
            )
        )

        launch_button = self.create_animated_button(
            f"Launch {app_name}", "#6272A4", "#7083C3"
        )
        launch_button.setVisible(False)
        launch_button.clicked.connect(
            lambda: self.launch_app(app_name, executable_prefix)
        )

        button_layout.addWidget(update_button)
        button_layout.addWidget(launch_button)
        info_layout.addLayout(button_layout)

        # Add info layout to card
        card_layout.addLayout(info_layout)

        # Another spacer to balance the layout
        card_layout.addStretch(1)

        card.setLayout(card_layout)

        # Store widgets for later use
        self.app_widgets[app_name] = {
            "label": app_label,
            "progress_bar": progress_bar,
            "update_button": update_button,
            "launch_button": launch_button,
        }

        # Initialize app state
        self.initialize_app(
            app_name,
            executable_prefix,
            app_label,
            progress_bar,
            update_button,
            launch_button,
        )

        return card

    def create_animated_button(self, text, color, hover_color):
        """
        Create an animated button with hover effects and fixed size.
        For long text, create a scrolling/marquee effect.
        """
        button = QPushButton(text)
        button.setFont(QFont("Arial", 14))
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: #FFFFFF;
                border-radius: 8px;
                padding: 10px 20px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """
        )
        button.setCursor(Qt.PointingHandCursor)

        # Set fixed size for all buttons - make them wider
        button.setFixedWidth(500)  # Increased from 200
        button.setFixedHeight(50)

        # For long text, set up a scrolling effect
        text_width = button.fontMetrics().horizontalAdvance(text)
        visible_width = button.width() - 40  # Account for padding

        if text_width > visible_width:
            # Store the original text
            button.original_text = text
            button.current_position = 0
            button.text_width = text_width
            button.visible_width = visible_width

            # Create timer for marquee effect
            button.scroll_timer = QTimer(button)
            button.scroll_timer.timeout.connect(
                lambda btn=button: self.scroll_button_text(btn)
            )

            # Start scrolling when hovered
            button.enterEvent = lambda e, btn=button: self.start_button_scroll(btn)
            button.leaveEvent = lambda e, btn=button: self.stop_button_scroll(btn)

        return button

    def scroll_button_text(self, button):
        """Handle scrolling text in buttons"""
        button.current_position += 1
        if button.current_position > len(button.original_text):
            button.current_position = 0

        # Create scrolling effect by showing a segment of text
        visible_text = button.original_text + "    " + button.original_text
        start_pos = button.current_position % (len(button.original_text) + 4)
        display_text = visible_text[
            start_pos : start_pos + 20
        ]  # Show only part of the text

        button.setText(display_text)

    def start_button_scroll(self, button):
        """Start scrolling text when button is hovered"""
        if hasattr(button, "scroll_timer"):
            button.scroll_timer.start(150)  # Scroll speed in milliseconds

    def stop_button_scroll(self, button):
        """Stop scrolling and reset text when mouse leaves button"""
        if hasattr(button, "scroll_timer"):
            button.scroll_timer.stop()
            button.setText(
                button.original_text[:20]
            )  # Truncate with ellipsis if needed

    def show_home_page(self):
        self.content_area.setCurrentIndex(0)

    def show_error_logs_page(self):
        self.load_error_logs()  # Reload logs each time the page is shown
        self.content_area.setCurrentIndex(1)

    def show_about_page(self):
        self.content_area.setCurrentIndex(2)

    def show_settings_page(self):
        self.content_area.setCurrentIndex(3)

    def exit_application(self):
        self.close()

    def initialize_app(
        self,
        app_name,
        executable_prefix,
        label,
        progress_bar,
        update_button,
        launch_button,
    ):
        """
        Initialize app state by checking local and remote versions.
        """
        label.setText(f"{app_name}: Checking local version...")
        local_version, local_filename = get_local_version(
            APPS_FOLDER, executable_prefix
        )

        if local_version:
            remote_version, _ = get_remote_version(app_name)

            if remote_version > local_version:
                label.setText(f"{app_name}: Update required.")
                update_button.setVisible(True)
                launch_button.setVisible(False)
            else:
                label.setText(f"{app_name}: Up to date.")
                update_button.setVisible(False)
                launch_button.setVisible(True)
        else:
            label.setText(f"{app_name}: Not installed. Please update.")
            update_button.setVisible(True)
            launch_button.setVisible(False)

    def update_app(self, app_name, executable_prefix, label, progress_bar):
        """
        Perform an update for the specified app.
        """
        try:
            label.setText(f"{app_name}: Updating...")
            progress_bar.setVisible(True)
            progress_bar.setValue(0)

            remote_version, remote_str = get_remote_version(app_name)
            download_new_version(
                APPS_FOLDER,
                executable_prefix,
                remote_str,
                progress_callback=lambda current, total: self.update_progress_bar(
                    progress_bar, current, total
                ),
            )

            label.setText(f"{app_name}: Update complete!")
            self.app_widgets[app_name]["update_button"].setVisible(False)
            self.app_widgets[app_name]["launch_button"].setVisible(True)
        except Exception as e:
            # Log the detailed error
            self.log_error(app_name, str(e))
            # Show simplified error message
            label.setText(f"{app_name}: Error occurred. Check logs.")
        finally:
            progress_bar.setVisible(False)

    def update_progress_bar(self, progress_bar, current, total):
        """
        Update the progress bar during updates.
        """
        percentage = int((current / total) * 100)
        progress_bar.setValue(percentage)

    def generate_key(self, password, salt):
        """Generate an encryption key from password and salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    def encrypt_file(self, input_file, output_file, key):
        """Encrypt a file using Fernet symmetric encryption"""
        fernet = Fernet(key)
        with open(input_file, "rb") as f:
            data = f.read()
        encrypted = fernet.encrypt(data)
        with open(output_file, "wb") as f:
            f.write(encrypted)

    def decrypt_file(self, input_file, output_file, key):
        """Decrypt a file using Fernet symmetric encryption"""
        fernet = Fernet(key)
        with open(input_file, "rb") as f:
            encrypted = f.read()
        decrypted = fernet.decrypt(encrypted)
        with open(output_file, "wb") as f:
            f.write(decrypted)

    def launch_app(self, app_name, executable_prefix):
        """
        Launch the specified app, first decrypting it to a temporary location.
        """
        local_version, local_filename = get_local_version(
            APPS_FOLDER, executable_prefix
        )
        if local_filename:
            # Path to encrypted app
            encrypted_app_path = os.path.join(APPS_FOLDER, local_filename)

            # Create a temporary path for the decrypted app
            temp_dir = os.path.join(os.environ["TEMP"], "app_control_temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_app_path = os.path.join(temp_dir, f"temp_{local_filename}")

            try:
                # Use a constant salt and password (in a real app, consider more secure approaches)
                salt = b"app_control_salt"
                password = b"this_is_a_secret_password_for_app_control"
                key = self.generate_key(password, salt)

                # Decrypt the app to the temporary location
                self.decrypt_file(encrypted_app_path, temp_app_path, key)

                # Launch the decrypted app
                process = subprocess.Popen([temp_app_path])

                # Set up a timer to remove the decrypted app after it launches
                def cleanup():
                    try:
                        # Check if the process is still running
                        if process.poll() is not None:
                            # Process has ended, delete the temporary file
                            if os.path.exists(temp_app_path):
                                os.remove(temp_app_path)
                            return
                        # If still running, check again later
                        QTimer.singleShot(5000, cleanup)
                    except Exception as e:
                        print(f"Cleanup error: {e}")

                # Start the cleanup timer
                QTimer.singleShot(5000, cleanup)

            except Exception as e:
                self.log_error(app_name, f"Failed to launch app: {str(e)}")
                self.app_widgets[app_name]["label"].setText(
                    f"{app_name}: Launch failed. See error logs."
                )
        else:
            self.app_widgets[app_name]["label"].setText(
                f"{app_name}: No version available to launch."
            )

    def load_error_logs(self):
        """Load and display error logs in a collapsible format"""
        # Clear existing logs
        while self.logs_layout.count():
            item = self.logs_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # If log file doesn't exist, create it
        if not os.path.exists(ERROR_LOG_FILE):
            with open(ERROR_LOG_FILE, "w") as f:
                json.dump([], f)

        # Load logs
        try:
            with open(ERROR_LOG_FILE, "r") as f:
                logs = json.load(f)

            if not logs:
                no_logs = QLabel("No errors have been logged yet")
                no_logs.setFont(QFont("Arial", 14))
                no_logs.setStyleSheet("color: #CCCCCC;")
                no_logs.setAlignment(Qt.AlignCenter)
                self.logs_layout.addWidget(no_logs)
                return

            # Group logs by date
            logs_by_date = {}
            for log in logs:
                date = log.get("date", "").split(" ")[0]  # Get just the date part
                if date not in logs_by_date:
                    logs_by_date[date] = []
                logs_by_date[date].append(log)

            # Sort dates and display newest first
            for date in sorted(logs_by_date.keys(), reverse=True):
                # Create collapsible section for each date
                date_header = CollapsibleSection(date)

                # Add each log entry for this date
                for log in logs_by_date[date]:
                    time = (
                        log.get("date", "").split(" ")[1]
                        if " " in log.get("date", "")
                        else ""
                    )
                    app_name = log.get("app", "Unknown")
                    error_msg = log.get("error", "Unknown error")

                    # Create log entry widget
                    entry = LogEntryWidget(time, app_name, error_msg)
                    date_header.addWidget(entry)

                self.logs_layout.addWidget(date_header)

        except Exception as e:
            error_label = QLabel(f"Error loading logs: {str(e)}")
            error_label.setStyleSheet("color: #FF5555;")
            self.logs_layout.addWidget(error_label)

    def clear_error_logs(self):
        """Clear all error logs"""
        with open(ERROR_LOG_FILE, "w") as f:
            json.dump([], f)
        self.load_error_logs()

    def log_error(self, app_name, error_msg):
        """Log an error to the error log file"""
        try:
            # Create logs directory if it doesn't exist
            os.makedirs(os.path.dirname(ERROR_LOG_FILE), exist_ok=True)

            # Load existing logs
            logs = []
            if os.path.exists(ERROR_LOG_FILE):
                with open(ERROR_LOG_FILE, "r") as f:
                    logs = json.load(f)

            # Add new log
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logs.append({"date": now, "app": app_name, "error": error_msg})

            # Write updated logs
            with open(ERROR_LOG_FILE, "w") as f:
                json.dump(logs, f)

        except Exception as e:
            print(f"Failed to log error: {str(e)}")


# Add these new classes at the end of the file
class CollapsibleSection(QWidget):
    """A collapsible section widget for grouping errors by date"""

    def __init__(self, title):
        super().__init__()
        self.setStyleSheet(
            """
            background-color: #2F344B;
            border-radius: 8px;
            margin: 2px;
        """
        )

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Header with toggle button
        self.header = QFrame()
        self.header.setStyleSheet(
            """
            QFrame {
                background-color: #3C3F58;
                border-radius: 8px;
                padding: 5px;
            }
            QFrame:hover {
                background-color: #44475A;
            }
        """
        )
        self.header.setCursor(Qt.PointingHandCursor)

        header_layout = QHBoxLayout(self.header)

        # Toggle icon
        self.toggle_icon = QLabel("▼")
        self.toggle_icon.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        header_layout.addWidget(self.toggle_icon)

        # Date label
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Content container
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 5, 10, 10)
        self.content_layout.setSpacing(5)

        # Add to main layout
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.content)

        # Connect header click to toggle
        self.header.mousePressEvent = self.toggle_content

        # Default to expanded
        self.is_expanded = True

    def toggle_content(self, event):
        self.is_expanded = not self.is_expanded
        self.content.setVisible(self.is_expanded)
        self.toggle_icon.setText("▼" if self.is_expanded else "►")

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)


class LogEntryWidget(QFrame):
    """Widget to display a single log entry with copy functionality"""

    def __init__(self, time, app_name, error_msg):
        super().__init__()
        self.error_msg = error_msg

        self.setStyleSheet(
            """
            QFrame {
                background-color: #2A2D45;
                border-radius: 5px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #31344E;
            }
        """
        )
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Time and app name
        header = QHBoxLayout()

        time_label = QLabel(time)
        time_label.setStyleSheet("color: #AAAAAA; font-weight: bold;")
        header.addWidget(time_label)

        app_label = QLabel(app_name)
        app_label.setStyleSheet("color: #FF79C6; font-weight: bold;")
        app_label.setAlignment(Qt.AlignRight)
        header.addWidget(app_label)

        layout.addLayout(header)

        # Error message
        error_label = QLabel(error_msg[:100] + ("..." if len(error_msg) > 100 else ""))
        error_label.setStyleSheet("color: #F8F8F2;")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)

        # Label to show when copied
        self.copy_label = QLabel("Copied! ✓")
        self.copy_label.setStyleSheet("color: #50FA7B; font-weight: bold;")
        self.copy_label.setAlignment(Qt.AlignRight)
        self.copy_label.hide()
        layout.addWidget(self.copy_label)

    def mousePressEvent(self, event):
        # Copy error to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.error_msg)

        # Show "Copied!" message briefly
        self.copy_label.show()
        QTimer.singleShot(1500, self.copy_label.hide)


if __name__ == "__main__":
    # Ensure apps folder exists
    os.makedirs(APPS_FOLDER, exist_ok=True)

    # Create a folder named "duck" on the C drive
    duck_folder = "C:\\duck"
    os.makedirs(duck_folder, exist_ok=True)
    print(f"Folder created at: {duck_folder}")

    # Start the application
    app = QApplication(sys.argv)
    window = AppControl()
    window.show()
    sys.exit(app.exec())
