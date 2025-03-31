import os
import sys
import subprocess  # Re-add this import
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QProgressBar, QFrame, QStackedWidget  # Update QStackedWidget import
)
from updater import get_local_version, get_remote_version, download_new_version

APPS_FOLDER = os.path.join(os.getcwd(), "apps")

APPS_CONFIG = [
    {"name": "WorkForce", "executable_prefix": "WorkForce_", "icon": "assets/workforce_icon.png"},
    {"name": "PersonnelManagement", "executable_prefix": "PersonnelManagement_", "icon": "assets/personnel_icon.png"}
]


class AppControl(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window properties
        self.setWindowTitle("App Version Control")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #23263A;")

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
        sidebar_container.setStyleSheet("""
            QFrame {
                background-color: #1E202D;
                border-right: 2px solid #2A2D45;
                padding: 10px;
            }
        """)
        self.central_layout.addWidget(sidebar_container, 0)

        # Content Area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #2A2D45; border-radius: 15px;")
        self.central_layout.addWidget(self.content_area, 1)

        # Add pages to content area
        self.create_home_page()
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
        self.create_sidebar_button("About", self.show_about_page)
        self.create_sidebar_button("Settings", self.show_settings_page)
        self.create_sidebar_button("Exit", self.exit_application)

    def create_sidebar_button(self, name, action):
        """
        Create a sidebar button.
        """
        btn = QPushButton(name)
        btn.setFont(QFont("Arial", 14))
        btn.setStyleSheet("""
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
        """)
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

        description = QLabel("App Control is a tool to manage and update your applications seamlessly.")
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
        card.setStyleSheet("""
            QFrame {
                background-color: #2F344B;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        card_layout = QHBoxLayout()

        # App Icon
        if os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(icon_path).scaled(100, 100, Qt.KeepAspectRatio))
            card_layout.addWidget(icon_label)

        # App Info and Buttons
        info_layout = QVBoxLayout()

        # App Name Label
        app_label = QLabel(app_name)
        app_label.setFont(QFont("Arial", 18, QFont.Bold))
        app_label.setStyleSheet("color: #FFFFFF;")
        info_layout.addWidget(app_label)

        # Progress Bar
        progress_bar = QProgressBar()
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2A2D45;
                border-radius: 5px;
                background-color: #44475A;
            }
            QProgressBar::chunk {
                background-color: #50FA7B;
            }
        """)
        progress_bar.setVisible(False)
        info_layout.addWidget(progress_bar)

        # Buttons
        button_layout = QHBoxLayout()
        update_button = self.create_animated_button(f"Update {app_name}", "#FF5555", "#FF6E6E")
        update_button.clicked.connect(lambda: self.update_app(app_name, executable_prefix, app_label, progress_bar))

        launch_button = self.create_animated_button(f"Launch {app_name}", "#6272A4", "#7083C3")
        launch_button.setVisible(False)
        launch_button.clicked.connect(lambda: self.launch_app(app_name, executable_prefix))

        button_layout.addWidget(update_button)
        button_layout.addWidget(launch_button)
        info_layout.addLayout(button_layout)

        # Add info layout to card
        card_layout.addLayout(info_layout)
        card.setLayout(card_layout)

        # Store widgets for later use
        self.app_widgets[app_name] = {
            "label": app_label,
            "progress_bar": progress_bar,
            "update_button": update_button,
            "launch_button": launch_button
        }

        # Initialize app state
        self.initialize_app(app_name, executable_prefix, app_label, progress_bar, update_button, launch_button)

        return card

    def create_animated_button(self, text, color, hover_color):
        """
        Create an animated button with hover effects.
        """
        button = QPushButton(text)
        button.setFont(QFont("Arial", 14))
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #FFFFFF;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def show_home_page(self):
        self.content_area.setCurrentIndex(0)

    def show_about_page(self):
        self.content_area.setCurrentIndex(1)

    def show_settings_page(self):
        self.content_area.setCurrentIndex(2)

    def exit_application(self):
        self.close()

    def initialize_app(self, app_name, executable_prefix, label, progress_bar, update_button, launch_button):
        """
        Initialize app state by checking local and remote versions.
        """
        label.setText(f"{app_name}: Checking local version...")
        local_version, local_filename = get_local_version(APPS_FOLDER, executable_prefix)

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
                APPS_FOLDER, executable_prefix, remote_str,
                progress_callback=lambda current, total: self.update_progress_bar(progress_bar, current, total)
            )

            label.setText(f"{app_name}: Update complete!")
            self.app_widgets[app_name]["update_button"].setVisible(False)
            self.app_widgets[app_name]["launch_button"].setVisible(True)
        except Exception as e:
            label.setText(f"{app_name}: Update failed: {str(e)}")
        finally:
            progress_bar.setVisible(False)

    def update_progress_bar(self, progress_bar, current, total):
        """
        Update the progress bar during updates.
        """
        percentage = int((current / total) * 100)
        progress_bar.setValue(percentage)

    def launch_app(self, app_name, executable_prefix):
        """
        Launch the specified app.
        """
        local_version, local_filename = get_local_version(APPS_FOLDER, executable_prefix)
        if local_filename:
            app_path = os.path.join(APPS_FOLDER, local_filename)
            subprocess.Popen([app_path])
        else:
            self.app_widgets[app_name]["label"].setText(f"{app_name}: No version available to launch.")


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