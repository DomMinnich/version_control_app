import os
import sys
import json
import datetime
import subprocess
import base64
import threading
import requests
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QProgressBar,
    QFrame,
    QStackedWidget,
    QScrollArea,
)
from updater import get_local_version, get_remote_version, download_new_version
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Global paths and server URL
APPS_FOLDER = os.path.join(os.getcwd(), "apps")
LOGS_FOLDER = os.path.join(os.getcwd(), "logs")
ERROR_LOG_FILE = os.path.join(LOGS_FOLDER, "error_log.json")
SERVER_URL = "http://127.0.0.1:5000"  # Update as needed


# ---------------------- Helper Functions ---------------------- #
def fetch_apps_config():
    """
    Fetch the apps configuration from the server.
    Returns a list of app configurations.
    """
    try:
        response = requests.get(f"{SERVER_URL}/apps", timeout=5)
        response.raise_for_status()
        config = response.json().get("apps", [])
        # Preserve the original asset filename by copying to "icon_filename"
        for app in config:
            if "icon" in app:
                app["icon_filename"] = app["icon"]
        return config
    except Exception as e:
        print("Error fetching app configuration from server:", e)
        # Fallback configuration if fetching fails
        fallback = [
            {
                "name": "WorkForce",
                "executable_prefix": "WorkForce_",
                "icon": "workforce_icon.png",
                "icon_filename": "workforce_icon.png",
            },
            {
                "name": "PersonnelManagement",
                "executable_prefix": "PersonnelManagement_",
                "icon": "personnel_icon.png",
                "icon_filename": "personnel_icon.png",
            },
        ]
        return fallback


def download_app_asset(asset_filename, local_folder):
    """
    Downloads the app's picture from the server and saves it in the local assets folder.
    Returns the path to a default icon if download fails.
    """
    local_path = os.path.join(local_folder, asset_filename)
    default_icon = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "default_app_icon.png"
    )

    try:
        asset_url = f"{SERVER_URL}/assets/{asset_filename}"
        response = requests.get(asset_url, timeout=5)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded/updated asset: {asset_filename}")
        return local_path
    except Exception as e:
        print(f"Failed to update asset {asset_filename}: {e}")
        # Create a default icon if it doesn't exist
        if not os.path.exists(default_icon):
            os.makedirs(os.path.dirname(default_icon), exist_ok=True)
            from PIL import Image

            img = Image.new("RGB", (100, 100), color=(99, 102, 241))
            img.save(default_icon)

        return default_icon


# ---------------------- Main Application ---------------------- #
class AppControl(QMainWindow):
    connection_status_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("App Version Control")
        self.setGeometry(100, 100, 1600, 800)
        self.setStyleSheet("background-color: #23263A;")

        # Ensure necessary folders exist
        os.makedirs(APPS_FOLDER, exist_ok=True)
        os.makedirs(LOGS_FOLDER, exist_ok=True)
        if not os.path.exists(ERROR_LOG_FILE):
            with open(ERROR_LOG_FILE, "w") as f:
                json.dump([], f)

        # Dynamic apps configuration from the server
        self.apps_config = fetch_apps_config()

        # Ensure local assets folder exists and update assets using the original filename
        self.assets_folder = os.path.join(os.getcwd(), "assets")
        os.makedirs(self.assets_folder, exist_ok=True)
        for app in self.apps_config:
            # Use the stored icon_filename rather than the possibly updated "icon" field.
            local_icon_path = download_app_asset(
                app["icon_filename"], self.assets_folder
            )
            app["icon"] = local_icon_path

        # Setup server connection checking
        self.server_connected = False
        self.connection_check_timer = QTimer(self)
        self.connection_check_timer.timeout.connect(self.check_server_connection)
        self.connection_check_timer.start(10000)
        self.connection_status_changed.connect(self.update_connection_status)

        # Setup main layout
        self.central_layout = QHBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self.central_layout)
        self.setCentralWidget(central_widget)

        # Create sidebar
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

        # Create content area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet(
            "background-color: #2A2D45; border-radius: 15px;"
        )
        self.central_layout.addWidget(self.content_area, 1)

        # Create pages
        self.create_home_page()
        self.create_error_logs_page()
        self.create_about_page()
        self.create_settings_page()

        self.running_processes = {}
        self.check_server_connection()
        QTimer.singleShot(500, self.check_server_connection)

    # ---------------------- Sidebar & Navigation ---------------------- #
    def create_sidebar(self):
        # Logo
        logo = QLabel()
        logo.setPixmap(
            QPixmap(os.path.join("assets", "logo.png")).scaled(
                100, 100, Qt.KeepAspectRatio
            )
        )
        logo.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(logo)

        # Connection status indicator
        self.connection_status = QFrame()
        self.connection_status.setFixedHeight(60)
        self.connection_status.setStyleSheet(
            """
            QFrame {
                border-radius: 12px;
                background-color: #33364D;
                margin: 10px;
                border: 1px solid #444760;
            }
        """
        )
        status_layout = QHBoxLayout(self.connection_status)
        status_layout.setContentsMargins(10, 0, 10, 0)
        status_layout.setSpacing(10)
        status_layout.setAlignment(Qt.AlignVCenter)
        self.status_icon = QLabel("●")
        self.status_icon.setFont(QFont("Arial", 20, QFont.Bold))
        self.status_icon.setStyleSheet("color: #FF5555;")
        status_layout.addWidget(self.status_icon)
        self.status_text = QLabel("Checking...")
        self.status_text.setFont(QFont("Arial", 16, QFont.Bold))
        self.status_text.setStyleSheet("color: #FFFFFF;")
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()
        refresh_btn = QPushButton("↻")
        refresh_btn.setToolTip("Check connection")
        refresh_btn.setFont(QFont("Arial", 14, QFont.Bold))
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #44475A;
                color: #FFFFFF;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #6272A4;
            }
        """
        )
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.check_server_connection_immediate)
        status_layout.addWidget(refresh_btn)
        self.sidebar_layout.addWidget(self.connection_status)

        # Navigation buttons
        self.create_sidebar_button("Home", self.show_home_page)
        self.create_sidebar_button("Error Logs", self.show_error_logs_page)
        self.create_sidebar_button("About", self.show_about_page)
        self.create_sidebar_button("Settings", self.show_settings_page)
        self.create_sidebar_button("Exit", self.exit_application)

    def create_sidebar_button(self, name, action):
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

    def show_home_page(self):
        self.content_area.setCurrentIndex(0)

    def show_error_logs_page(self):
        self.load_error_logs()
        self.content_area.setCurrentIndex(1)

    def show_about_page(self):
        self.content_area.setCurrentIndex(2)

    def show_settings_page(self):
        self.content_area.setCurrentIndex(3)

    def exit_application(self):
        self.close()

    # ---------------------- Pages Creation ---------------------- #
    def create_home_page(self):
        home_page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)
        header = QLabel("App Management")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Create a scrollable area for app cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:horizontal {
                background-color: #2A2D45;
                height: 15px;
                margin: 3px 15px 3px 15px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background-color: #44475A;
                min-width: 30px;
                border-radius: 4px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 10px;
                border: none;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """
        )

        # Container widget for app cards
        apps_container = QWidget()
        apps_layout = QHBoxLayout(apps_container)
        apps_layout.setSpacing(20)
        apps_layout.setAlignment(Qt.AlignLeft)
        apps_layout.setContentsMargins(10, 5, 10, 5)

        self.app_widgets = {}
        # Create a card for each app from dynamic configuration
        for app in self.apps_config:
            apps_layout.addWidget(self.create_app_card(app))

        # Add some spacing at the end for better scrolling experience
        spacer = QWidget()
        spacer.setFixedWidth(10)
        apps_layout.addWidget(spacer)

        # Only show scrollbar if more than 2 apps
        if len(self.apps_config) > 2:
            scroll_area.setWidget(apps_container)
            layout.addWidget(scroll_area)
        else:
            # For 2 or fewer apps, just add them directly to the layout
            for app in self.apps_config:
                layout.addWidget(self.create_app_card(app))

        # Add indicator dots for navigation when there are more than 2 apps
        if len(self.apps_config) > 2:
            dots_widget = QWidget()
            dots_layout = QHBoxLayout(dots_widget)
            dots_layout.setAlignment(Qt.AlignCenter)
            dots_layout.setSpacing(10)

            for i in range(len(self.apps_config)):
                dot = QLabel("•")
                dot.setStyleSheet("color: #6272A4; font-size: 20px;")
                dots_layout.addWidget(dot)

            layout.addWidget(dots_widget)

        self.add_footer(layout)
        home_page.setLayout(layout)
        self.content_area.addWidget(home_page)

    def create_about_page(self):
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
        settings_page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        placeholder = QLabel("Settings...")
        placeholder.setFont(QFont("Arial", 16))
        placeholder.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(placeholder)
        self.add_footer(layout)
        settings_page.setLayout(layout)
        self.content_area.addWidget(settings_page)

    def create_error_logs_page(self):
        error_page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        header = QLabel("Error Logs")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
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
        self.logs_container = QWidget()
        self.logs_layout = QVBoxLayout(self.logs_container)
        self.logs_layout.setAlignment(Qt.AlignTop)
        self.logs_layout.setSpacing(10)
        self.load_error_logs()
        scroll_area.setWidget(self.logs_container)
        layout.addWidget(scroll_area)
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
        footer = QLabel("Developed by Dominic Minnich")
        footer.setFont(QFont("Arial", 10))
        footer.setStyleSheet("color: #CCCCCC; margin-top: 20px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    # ---------------------- App Card & Functionality ---------------------- #
    def create_app_card(self, app_config):
        app_name = app_config["name"]
        executable_prefix = app_config["executable_prefix"]
        icon_path = app_config.get("icon", "")

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
        card_layout.setAlignment(Qt.AlignLeft)
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            else:
                print(f"Warning: Null pixmap for {icon_path}")
                icon_label.setText(app_name[0])
                icon_label.setStyleSheet(
                    "background-color: #6272A4; color: white; font-size: 40px; font-weight: bold; border-radius: 50px;"
                )
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(100, 100)
        icon_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        card_layout.addWidget(icon_label)
        card_layout.addStretch(1)
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)
        app_label = QLabel(app_name)
        app_label.setFont(QFont("Arial", 18, QFont.Bold))
        app_label.setStyleSheet("color: #FFFFFF;")
        app_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(app_label)
        progress_bar = QProgressBar()
        progress_bar.setTextVisible(False)
        progress_bar.setFixedWidth(300)
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
        info_layout.addWidget(progress_bar, 0, Qt.AlignCenter)
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
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
        card_layout.addLayout(info_layout)
        card_layout.addStretch(1)
        card.setLayout(card_layout)
        # Store widget references for later updates
        self.app_widgets[app_name] = {
            "label": app_label,
            "progress_bar": progress_bar,
            "update_button": update_button,
            "launch_button": launch_button,
            "icon_label": icon_label,
        }
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
        button.setFixedWidth(500)
        button.setFixedHeight(50)
        text_width = button.fontMetrics().horizontalAdvance(text)
        visible_width = button.width() - 40
        if text_width > visible_width:
            button.original_text = text
            button.current_position = 0
            button.text_width = text_width
            button.visible_width = visible_width
            button.scroll_timer = QTimer(button)
            button.scroll_timer.timeout.connect(
                lambda btn=button: self.scroll_button_text(btn)
            )
            button.enterEvent = lambda e, btn=button: self.start_button_scroll(btn)
            button.leaveEvent = lambda e, btn=button: self.stop_button_scroll(btn)
        return button

    def scroll_button_text(self, button):
        button.current_position += 1
        if button.current_position > len(button.original_text):
            button.current_position = 0
        visible_text = button.original_text + "    " + button.original_text
        start_pos = button.current_position % (len(button.original_text) + 4)
        display_text = visible_text[start_pos : start_pos + 20]
        button.setText(display_text)

    def start_button_scroll(self, button):
        if hasattr(button, "scroll_timer"):
            button.scroll_timer.start(150)

    def stop_button_scroll(self, button):
        if hasattr(button, "scroll_timer"):
            button.scroll_timer.stop()
            button.setText(button.original_text[:20])

    def initialize_app(
        self,
        app_name,
        executable_prefix,
        label,
        progress_bar,
        update_button,
        launch_button,
    ):
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
            label.setText(f"{app_name}: Not installed.")
            update_button.setVisible(True)
            launch_button.setVisible(False)

    def update_app(self, app_name, executable_prefix, label, progress_bar):
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
            # After updating the executable, update the asset icon.
            app_config = next(
                (a for a in self.apps_config if a["name"] == app_name), None
            )
            if app_config:
                # Use the original asset filename stored in icon_filename.
                local_icon = download_app_asset(
                    app_config["icon_filename"], self.assets_folder
                )
                app_config["icon"] = local_icon
                if "icon_label" in self.app_widgets[app_name]:
                    pixmap = QPixmap(local_icon)
                    if not pixmap.isNull():
                        self.app_widgets[app_name]["icon_label"].setPixmap(
                            pixmap.scaled(100, 100, Qt.KeepAspectRatio)
                        )
                    else:
                        icon_label = self.app_widgets[app_name]["icon_label"]
                        icon_label.setText(app_name[0])
                        icon_label.setStyleSheet(
                            "background-color: #6272A4; color: white; font-size: 40px; font-weight: bold; border-radius: 50px;"
                        )
                        icon_label.setAlignment(Qt.AlignCenter)
                        icon_label.setFixedSize(100, 100)
            label.setText(f"{app_name}: Update complete!")
            self.app_widgets[app_name]["update_button"].setVisible(False)
            self.app_widgets[app_name]["launch_button"].setVisible(True)
        except Exception as e:
            self.log_error(app_name, str(e))
            label.setText(f"{app_name}: Error occurred. Check logs.")
        finally:
            progress_bar.setVisible(False)

    def update_progress_bar(self, progress_bar, current, total):
        percentage = int((current / total) * 100)
        progress_bar.setValue(percentage)

    def generate_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    def encrypt_file(self, input_file, output_file, key):
        fernet = Fernet(key)
        with open(input_file, "rb") as f:
            data = f.read()
        encrypted = fernet.encrypt(data)
        with open(output_file, "wb") as f:
            f.write(encrypted)

    def decrypt_file(self, input_file, output_file, key):
        fernet = Fernet(key)
        with open(input_file, "rb") as f:
            encrypted = f.read()
        decrypted = fernet.decrypt(encrypted)
        with open(output_file, "wb") as f:
            f.write(decrypted)

    def launch_app(self, app_name, executable_prefix):
        if (
            app_name in self.running_processes
            and self.running_processes[app_name].poll() is None
        ):
            self.app_widgets[app_name]["label"].setText(f"{app_name}: Already running.")
            return
        local_version, local_filename = get_local_version(
            APPS_FOLDER, executable_prefix
        )
        if local_filename:
            encrypted_app_path = os.path.join(APPS_FOLDER, local_filename)
            temp_dir = os.path.join(os.environ["TEMP"], "app_control_temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_app_path = os.path.join(temp_dir, f"temp_{local_filename}")
            try:
                salt = b"app_control_salt"
                password = b"this_is_a_secret_password_for_app_control"
                key = self.generate_key(password, salt)
                self.decrypt_file(encrypted_app_path, temp_app_path, key)
                process = subprocess.Popen([temp_app_path])
                self.running_processes[app_name] = process
                self.app_widgets[app_name]["label"].setText(f"{app_name}: Running...")

                def cleanup():
                    try:
                        if process.poll() is not None:
                            if os.path.exists(temp_app_path):
                                os.remove(temp_app_path)
                            if app_name in self.running_processes:
                                del self.running_processes[app_name]
                            self.app_widgets[app_name]["label"].setText(
                                f"{app_name}: Ready to launch."
                            )
                            return
                        QTimer.singleShot(5000, cleanup)
                    except Exception as e:
                        print(f"Cleanup error: {e}")

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

    # ---------------------- Error Logging ---------------------- #
    def load_error_logs(self):
        while self.logs_layout.count():
            item = self.logs_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not os.path.exists(ERROR_LOG_FILE):
            with open(ERROR_LOG_FILE, "w") as f:
                json.dump([], f)
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
            logs_by_date = {}
            for log in logs:
                date = log.get("date", "").split(" ")[0]
                if date not in logs_by_date:
                    logs_by_date[date] = []
                logs_by_date[date].append(log)
            for date in sorted(logs_by_date.keys(), reverse=True):
                date_header = CollapsibleSection(date)
                for log in logs_by_date[date]:
                    time_str = (
                        log.get("date", "").split(" ")[1]
                        if " " in log.get("date", "")
                        else ""
                    )
                    app_name = log.get("app", "Unknown")
                    error_msg = log.get("error", "Unknown error")
                    entry = LogEntryWidget(time_str, app_name, error_msg)
                    date_header.addWidget(entry)
                self.logs_layout.addWidget(date_header)
        except Exception as e:
            error_label = QLabel(f"Error loading logs: {str(e)}")
            error_label.setStyleSheet("color: #FF5555;")
            self.logs_layout.addWidget(error_label)

    def clear_error_logs(self):
        with open(ERROR_LOG_FILE, "w") as f:
            json.dump([], f)
        self.load_error_logs()

    def log_error(self, app_name, error_msg):
        try:
            os.makedirs(os.path.dirname(ERROR_LOG_FILE), exist_ok=True)
            logs = []
            if os.path.exists(ERROR_LOG_FILE):
                with open(ERROR_LOG_FILE, "r") as f:
                    logs = json.load(f)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logs.append({"date": now, "app": app_name, "error": error_msg})
            with open(ERROR_LOG_FILE, "w") as f:
                json.dump(logs, f)
        except Exception as e:
            print(f"Failed to log error: {str(e)}")

    # ---------------------- Server Connection Checking ---------------------- #
    def check_server_connection_immediate(self):
        self.status_text.setText("Checking...")
        self.status_icon.setStyleSheet("color: #FFCC00;")
        if (
            hasattr(self, "connection_check_thread")
            and self.connection_check_thread.is_alive()
        ):
            return
        self.check_server_connection()

    def check_server_connection(self):
        """
        Check if we can connect to the server and update the status indicator.
        """
        #  print("Starting server connection check...")

        def do_check():
            try:
                #         print("Attempting to connect to server...")
                response = requests.get(SERVER_URL, timeout=2)
                if response.status_code == 200:
                    #             print(f"Connection successful: {response.status_code}")
                    connected = True
                else:
                    print(f"Server returned error status: {response.status_code}")
                    connected = False
            except requests.exceptions.ConnectionError:
                print("Connection refused: Server is not running")
                connected = False
            except requests.exceptions.Timeout:
                print("Connection timeout")
                connected = False
            except Exception as e:
                print(f"Connection check failed: {str(e)}")
                connected = False

            self.connection_status_changed.emit(connected)

        self.connection_check_thread = threading.Thread(target=do_check, daemon=True)
        self.connection_check_thread.start()

    def update_connection_status(self, connected):
        self.server_connected = connected
        if connected:
            self._set_connected_status()
        else:
            self._set_disconnected_status()

    def _set_connected_status(self):
        #   print("[DEBUG] UI updated: CONNECTED")
        self.connection_status.setStyleSheet(
            """
            QFrame {
                border-radius: 12px;
                background-color: rgba(80, 250, 123, 0.15);
                margin: 5px 10px 10px 10px;
                border: 1px solid rgba(80, 250, 123, 0.5);
            }
        """
        )
        self.status_icon.setStyleSheet("color: #50FA7B;")
        self.status_text.setText("Connected")
        self.status_text.setStyleSheet(
            "color: #50FA7B; font-size: 20px; font-weight: bold;"
        )
        self.start_connection_animation()

    def _set_disconnected_status(self):
        print("[DEBUG] UI updated: DISCONNECTED")
        self.connection_status.setStyleSheet(
            """
            QFrame {
                border-radius: 12px;
                background-color: rgba(255, 85, 85, 0.15);
                margin: 5px 10px 15px 10px;
                border: 1px solid rgba(255, 85, 85, 0.5);
            }
        """
        )
        self.status_icon.setStyleSheet("color: #FF5555;")
        self.status_text.setText("Disconnected")

    def start_connection_animation(self):
        def pulse_animation():
            if not self.server_connected:
                return
            current_style = self.status_icon.styleSheet()
            if "rgba(80, 250, 123, 0.6)" in current_style:
                self.status_icon.setStyleSheet("color: #50FA7B;")
            else:
                self.status_icon.setStyleSheet("color: rgba(80, 250, 123, 0.6);")
            if self.server_connected:
                QTimer.singleShot(800, pulse_animation)

        pulse_animation()


# ---------------------- Collapsible Sections for Logs ---------------------- #
class CollapsibleSection(QWidget):
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
        self.toggle_icon = QLabel("▼")
        self.toggle_icon.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        header_layout.addWidget(self.toggle_icon)
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 5, 10, 10)
        self.content_layout.setSpacing(5)
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.content)
        self.header.mousePressEvent = self.toggle_content
        self.is_expanded = True

    def toggle_content(self, event):
        self.is_expanded = not self.is_expanded
        self.content.setVisible(self.is_expanded)
        self.toggle_icon.setText("▼" if self.is_expanded else "►")

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)


class LogEntryWidget(QFrame):
    def __init__(self, time_str, app_name, error_msg):
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
        header = QHBoxLayout()
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #AAAAAA; font-weight: bold;")
        header.addWidget(time_label)
        app_label = QLabel(app_name)
        app_label.setStyleSheet("color: #FF79C6; font-weight: bold;")
        app_label.setAlignment(Qt.AlignRight)
        header.addWidget(app_label)
        layout.addLayout(header)
        error_label = QLabel(error_msg[:100] + ("..." if len(error_msg) > 100 else ""))
        error_label.setStyleSheet("color: #F8F8F2;")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        self.copy_label = QLabel("Copied! ✓")
        self.copy_label.setStyleSheet("color: #50FA7B; font-weight: bold;")
        self.copy_label.setAlignment(Qt.AlignRight)
        self.copy_label.hide()
        layout.addWidget(self.copy_label)

    def mousePressEvent(self, event):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.error_msg)
        self.copy_label.show()
        QTimer.singleShot(1500, self.copy_label.hide)


# ---------------------- Main Entry Point ---------------------- #
if __name__ == "__main__":
    # Create a folder named "duck" on the C drive as per your original code
    duck_folder = "C:\\duck"
    os.makedirs(duck_folder, exist_ok=True)
    print(f"Folder created at: {duck_folder}")

    app = QApplication(sys.argv)
    window = AppControl()
    window.show()
    sys.exit(app.exec_())
