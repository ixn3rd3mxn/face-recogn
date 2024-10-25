import sys
import cv2
import os
import numpy as np
import firebase_admin
from firebase_admin import credentials, db, storage
import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from PySide6 import QtCore, QtGui, QtWidgets

from BlurWindow.blurWindow import blur  # Import the blur module

from google.auth.transport.requests import Request
import ezsheets
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from collections import defaultdict
from googleapiclient.http import MediaFileUpload

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://testfux-f7e98-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "testfux-f7e98.appspot.com"
})

# Create a FaceDetector object
CONFIDENCE_THRESHOLD = 0.7
base_options = python.BaseOptions(model_asset_path='detector.tflite')
options = vision.FaceDetectorOptions(base_options=base_options, min_detection_confidence=CONFIDENCE_THRESHOLD)
detector = vision.FaceDetector.create_from_options(options)

# Reference to the Firebase Realtime Database
ref = db.reference('human')

# Constant values for total_attendance and last_attendance_time
total_attendance = 0
last_attendance_time = "0001-01-01 01:01:01"

SCOPES = ['https://www.googleapis.com/auth/drive']

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1015, 665)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.title_frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.title_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.title_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.title_frame.setObjectName("title_frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.title_frame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.title_icon = QtWidgets.QLabel(parent=self.title_frame)
        self.title_icon.setObjectName("title_icon")
        self.horizontalLayout.addWidget(self.title_icon)
        self.title_label = QtWidgets.QLabel(parent=self.title_frame)
        self.title_label.setObjectName("title_label")
        self.horizontalLayout.addWidget(self.title_label)
        self.menu_btn = QtWidgets.QPushButton(parent=self.title_frame)
        self.menu_btn.setObjectName("menu_btn")
        self.horizontalLayout.addWidget(self.menu_btn)
        self.gridLayout.addWidget(self.title_frame, 0, 0, 1, 2)
        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.centralwidget)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page = QtWidgets.QWidget()
        self.page.setObjectName("page")
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName("page_2")
        self.stackedWidget.addWidget(self.page_2)
        self.gridLayout.addWidget(self.stackedWidget, 0, 2, 2, 1)
        self.listWidget_icon_only = QtWidgets.QListWidget(parent=self.centralwidget)
        self.listWidget_icon_only.setMaximumSize(QtCore.QSize(55, 16777215))
        self.listWidget_icon_only.setObjectName("listWidget_icon_only")
        self.gridLayout.addWidget(self.listWidget_icon_only, 1, 0, 1, 1)
        self.listWidget = QtWidgets.QListWidget(parent=self.centralwidget)
        self.listWidget.setMaximumSize(QtCore.QSize(200, 16777215))
        self.listWidget.setObjectName("listWidget")
        self.gridLayout.addWidget(self.listWidget, 1, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 875, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.title_icon.setText(_translate("MainWindow", "TextLabel"))
        self.title_label.setText(_translate("MainWindow", "TextLabel"))
        self.menu_btn.setText(_translate("MainWindow", "PushButton"))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize the UI from the generated 'main_ui' class
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Enable the blur effect
        self.setAttribute(Qt.WA_TranslucentBackground)
        hWnd = self.winId()
        blur(hWnd, Acrylic=True)  # Apply the blur effect
        #blur(hWnd, Acrylic=True)

        # Set window properties
        self.setWindowIcon(QIcon("./icon/WindowIcon.ico"))
        self.setWindowTitle("Admin AIO GUI")

        # Sidebar and menu setup
        self.title_label = self.ui.title_label
        self.title_label.setText("Admin AIO")

        self.title_icon = self.ui.title_icon
        self.title_icon.setText("")
        self.title_icon.setPixmap(QPixmap("./icon/SidebarIcon.png"))
        self.title_icon.setScaledContents(True)

        self.side_menu = self.ui.listWidget
        self.side_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.side_menu_icon_only = self.ui.listWidget_icon_only
        self.side_menu_icon_only.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.side_menu_icon_only.hide()

        self.menu_btn = self.ui.menu_btn
        self.menu_btn.setText("")
        self.menu_btn.setIcon(QIcon("./icon/ListTab.ico"))
        self.menu_btn.setIconSize(QSize(30, 30))
        self.menu_btn.setCheckable(True)
        self.menu_btn.setChecked(False)

        self.main_content = self.ui.stackedWidget

        # Define a list of menu items with names and icons
        self.menu_list = [
            {"name": "  Manage User", "icon": "./icon/ListUser.ico"},
            {"name": "  Manage Sheet", "icon": "./icon/sheet.ico"},  # New menu item for Sheet Management
            {"name": "  Setting", "icon": "./icon/ResetAll.ico"}
        ]

        # Initialize the UI elements and slots
        self.init_list_widget()
        self.init_stackwidget()
        self.init_single_slot()

        self.init_manage_users()
        self.init_manage_sheet()

        # Apply initial style
        self.apply_style_sheet()

    def apply_style_sheet(self):
        # Adjust the style to match the blur effect
        self.setStyleSheet("""


            QTextEdit {
                background-color: transparent;
                color: white;
            }


            QLabel {
                background-color: transparent;
                color: white;
            }
        """)

    def init_single_slot(self):
        # Connect signals and slots for menu button and side menu
        self.menu_btn.toggled['bool'].connect(self.side_menu.setHidden)
        self.menu_btn.toggled['bool'].connect(self.title_label.setHidden)
        self.menu_btn.toggled['bool'].connect(self.side_menu_icon_only.setVisible)
        self.menu_btn.toggled['bool'].connect(self.title_icon.setHidden)

        # Connect signals and slots for switching between menu items
        self.side_menu.currentRowChanged['int'].connect(self.main_content.setCurrentIndex)
        self.side_menu_icon_only.currentRowChanged['int'].connect(self.main_content.setCurrentIndex)
        self.side_menu.currentRowChanged['int'].connect(self.side_menu_icon_only.setCurrentRow)
        self.side_menu_icon_only.currentRowChanged['int'].connect(self.side_menu.setCurrentRow)
        self.menu_btn.toggled.connect(self.button_icon_change)

    def init_list_widget(self):
        # Initialize the side menu and side menu with icons only
        self.side_menu_icon_only.clear()
        self.side_menu.clear()

        for menu in self.menu_list:
            # Set items for the side menu with icons only
            item = QListWidgetItem()
            item.setIcon(QIcon(menu.get("icon")))
            item.setSizeHint(QSize(40, 40))
            self.side_menu_icon_only.addItem(item)
            self.side_menu_icon_only.setCurrentRow(0)

            # Set items for the side menu with icons and text
            item_new = QListWidgetItem()
            item_new.setIcon(QIcon(menu.get("icon")))
            item_new.setText(menu.get("name"))
            self.side_menu.addItem(item_new)
            self.side_menu.setCurrentRow(0)

    def init_stackwidget(self):
        # Initialize the stack widget with custom pages (actual functionality)
        widget_list = self.main_content.findChildren(QWidget)
        for widget in widget_list:
            self.main_content.removeWidget(widget)

        # Custom pages from the original implementation
        self.page_manage_users = QWidget()
        self.page_manage_sheets = QWidget()  # New page for Sheet Management
        self.page_setting = QWidget()  # Settings page

        # Add custom pages to the stack widget
        self.main_content.addWidget(self.page_manage_users)
        self.main_content.addWidget(self.page_manage_sheets)  # Add the new page to the stack widget
        self.main_content.addWidget(self.page_setting)

        # Initialize the settings page
        self.init_settings_page()

    def button_icon_change(self, status):
        # Change the menu button icon based on its status
        if status:
            self.menu_btn.setIcon(QIcon("./icon/ListTab.ico"))
        else:
            self.menu_btn.setIcon(QIcon("./icon/ListTab.ico"))

        # Optionally, resize icons based on the sidebar's state
        if status:  # Sidebar is collapsed
            self.menu_btn.setIconSize(QSize(30, 30))  # Smaller icon size for collapsed state
        else:  # Sidebar is expanded
            self.menu_btn.setIconSize(QSize(35, 35))  # Larger icon size for expanded state

    def update_user_list(self):
        # Clear the table before populating
        self.user_table.setRowCount(0)

        # Fetch user data from Firebase
        students = ref.get()
        if students:
            for student_id, student_data in students.items():
                row_position = self.user_table.rowCount()
                self.user_table.insertRow(row_position)

                # Create and add non-editable items to the table
                id_item = QTableWidgetItem(student_id)
                name_item = QTableWidgetItem(student_data.get('human_name', ''))
                attendance_item = QTableWidgetItem(str(student_data.get('human_total_attendance', 0)))
                time_item = QTableWidgetItem(student_data.get('human_last_attendance_time', ''))
                punctual_item = QTableWidgetItem(str(student_data.get('punctual_attendance', 0)))
                late_item = QTableWidgetItem(str(student_data.get('late_attendance', 0)))
                finish_item = QTableWidgetItem(str(student_data.get('finish_attendance', 0)))  # New field
                enter_work_item = QTableWidgetItem(str(student_data.get('Enter_work', 8)))  # Default to 8 if not set
                leave_work_item = QTableWidgetItem(str(student_data.get('Leave_work', 17)))  # Default to 17 if not set

                # Set flags to make them non-editable
                for item in [id_item, name_item, attendance_item, time_item, punctual_item, late_item, finish_item, enter_work_item, leave_work_item]:
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

                # Add items to the table
                self.user_table.setItem(row_position, 0, id_item)
                self.user_table.setItem(row_position, 1, name_item)
                self.user_table.setItem(row_position, 2, attendance_item)
                self.user_table.setItem(row_position, 3, punctual_item)
                self.user_table.setItem(row_position, 4, late_item)
                self.user_table.setItem(row_position, 5, finish_item)  # Add this line
                self.user_table.setItem(row_position, 6, enter_work_item)
                self.user_table.setItem(row_position, 7, leave_work_item)
                self.user_table.setItem(row_position, 8, time_item)

    def init_manage_users(self):
        layout = QVBoxLayout(self.page_manage_users)

        # Create a table widget with columns for the new data fields
        self.user_table = QTableWidget(0, 9)  # Update column count to 9
        self.user_table.setHorizontalHeaderLabels([
            "ID", "Name", "Total attend", "Punctual attend", "Late attend", "Finish attend", "Enter Work", "Leave Work", "Last attend Time"
        ])

        # Adjust column widths for proper space allocation
        self.user_table.setColumnWidth(0, 30)
        self.user_table.setColumnWidth(1, 120)
        self.user_table.setColumnWidth(2, 80)
        self.user_table.setColumnWidth(3, 100)
        self.user_table.setColumnWidth(4, 80)
        self.user_table.setColumnWidth(5, 80)  # New column for Finish Attendance
        self.user_table.setColumnWidth(6, 80)
        self.user_table.setColumnWidth(7, 80)
        self.user_table.setColumnWidth(8, 120)
        layout.addWidget(self.user_table)

        # Create a horizontal layout for all the buttons
        button_layout = QHBoxLayout()

        # Add the buttons to the horizontal layout
        self.add_user_btn = QPushButton("Add User")
        button_layout.addWidget(self.add_user_btn)

        self.update_user_btn = QPushButton("Update User")
        button_layout.addWidget(self.update_user_btn)

        self.delete_user_btn = QPushButton("Delete User")
        button_layout.addWidget(self.delete_user_btn)

        self.reset_user_btn = QPushButton("Reset User")
        button_layout.addWidget(self.reset_user_btn)

        self.reset_all_users_btn = QPushButton("Reset All Users")
        button_layout.addWidget(self.reset_all_users_btn)

        self.view_image_btn = QPushButton("View Image")
        button_layout.addWidget(self.view_image_btn)

        self.refresh_btn = QPushButton("Refresh")
        button_layout.addWidget(self.refresh_btn)

        # Add the horizontal button layout to the main vertical layout
        layout.addLayout(button_layout)

        # Usage info
        usage_layout = QHBoxLayout()
        self.database_label = QLabel("Realtime Database usage loading...", self)
        self.storage_label = QLabel("Cloud Storage usage loading...", self)
        usage_layout.addWidget(self.database_label)
        usage_layout.addWidget(self.storage_label)
        layout.addLayout(usage_layout)

        # Connect the button clicks to their respective functions
        self.add_user_btn.clicked.connect(self.show_add_user_options)
        self.update_user_btn.clicked.connect(self.update_user)
        self.delete_user_btn.clicked.connect(self.delete_user)
        self.reset_user_btn.clicked.connect(self.reset_user)
        self.reset_all_users_btn.clicked.connect(self.reset_all_users)
        self.view_image_btn.clicked.connect(self.view_image)
        self.refresh_btn.clicked.connect(self.update_user_list)  # Connect the refresh button to update_user_list
        self.refresh_btn.clicked.connect(self.fetch_firebase_usage)  # Refresh Firebase usage data when the refresh button is clicked

        # Fetch and display user data in the table
        self.update_user_list()

        # Fetch Firebase usage details
        self.fetch_firebase_usage()

    def show_add_user_options(self):
        # Create a dialog with two options: "Auto Increment ID" and "Manual ID"
        msg_box = QMessageBox(self)  # Pass 'self' to center it over the main window
        msg_box.setWindowTitle("Add User")
        msg_box.setText("Choose how to add a user:")

        # Add buttons for "Auto Increment ID" and "Manual ID"
        auto_btn = msg_box.addButton("Auto Increment ID", QMessageBox.ButtonRole.ActionRole)
        manual_btn = msg_box.addButton("Manual ID", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg_box.addButton(QMessageBox.StandardButton.Cancel)

        # Show the dialog and wait for the user's selection
        msg_box.exec()

        # Check which button was clicked and call the appropriate function
        if msg_box.clickedButton() == auto_btn:
            self.add_user_auto()
        elif msg_box.clickedButton() == manual_btn:
            self.add_user_manual()
        else:
            # Cancel button was pressed; do nothing
            pass

    def add_user_auto(self):
        user_id = self.find_next_available_id()
        user_name, ok = QInputDialog.getText(self, 'Enter User Name', 'User Name:')
        if ok and user_name:
            self.add_user_to_firebase(user_id, user_name)
            self.update_user_list()  # Refresh user list
            self.fetch_firebase_usage()

    def find_next_available_id(self):
        students = ref.get()
        
        # Handle the case where students is None (no user data)
        if not students:
            return '001'
        
        # Extract existing IDs and sort them as integers
        existing_ids = sorted([int(key) for key in students.keys() if key.isdigit()])

        # Find the closest available ID in the sequence
        for i in range(1, len(existing_ids) + 2):
            if i not in existing_ids:
                return f'{i:03d}'  # Format the ID as a three-digit number (e.g., '002')

        # Fallback in case of an unexpected situation
        return f'{len(existing_ids) + 1:03d}'
    
    def add_user_manual(self):
        while True:
            # Prompt the user for the ID and validate the input
            user_id, ok = QInputDialog.getText(self, 'Enter User ID', 'User ID (e.g., 001):')
            if not ok:
                return  # Cancel if the user doesn't proceed

            # Check if the input is empty
            if not user_id.strip():
                QMessageBox.warning(self, "Error", "ID cannot be empty. Please enter a valid numeric ID.")
                continue

            # Check if the input contains only digits
            if not user_id.isdigit():
                QMessageBox.warning(self, "Error", "ID must contain only numbers. Please enter a valid numeric ID.")
                continue

            # Format the ID to always be 3 digits (e.g., '1' becomes '001')
            user_id = f'{int(user_id):03d}'

            # Check if the ID already exists in Firebase
            if ref.child(user_id).get() is not None:
                QMessageBox.warning(self, "Error", "ID already exists. Please enter a new ID.")
            else:
                break  # If everything is valid, break the loop

        # Now prompt for the user name
        user_name, ok = QInputDialog.getText(self, 'Enter User Name', 'User Name:')
        if ok and user_name.strip():
            self.add_user_to_firebase(user_id, user_name)
            self.update_user_list()  # Refresh the user list
            self.fetch_firebase_usage()
        else:
            QMessageBox.warning(self, "Error", "User name cannot be empty. Please enter a valid name.")

    def add_user_to_firebase(self, user_id, user_name):
        # Add user to Firebase
        punctual_attendance = 0
        late_attendance = 0
        finish_attendance = 0  # Initialize the new field

        # Prompt user for work time setup option
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Work Time Setup")
        msg_box.setText("Choose how to set work time:")
        auto_btn = msg_box.addButton("Auto Default (8-17)", QMessageBox.ButtonRole.ActionRole)
        manual_btn = msg_box.addButton("Manual", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg_box.addButton(QMessageBox.StandardButton.Cancel)

        msg_box.exec()
        if msg_box.clickedButton() == auto_btn:
            enter_work = 8
            leave_work = 17
        elif msg_box.clickedButton() == manual_btn:
            # Prompt for manual entry
            enter_work, ok1 = QInputDialog.getInt(
                self, 
                "Enter Work Time", 
                "Enter start time (0-23):", 
                minValue=0, maxValue=23
            )
            leave_work, ok2 = QInputDialog.getInt(
                self, 
                "Leave Work Time", 
                "Enter end time (0-23):", 
                minValue=0, maxValue=23
            )
            if not (ok1 and ok2):
                QMessageBox.warning(self, "Error", "Invalid time input. Please try again.")
                return
        else:
            # Cancel button was pressed
            return

        new_user_data = {
            "human_name": user_name,
            "human_total_attendance": 0,
            "human_last_attendance_time": "0001-01-01 01:01:01",
            "punctual_attendance": punctual_attendance,
            "late_attendance": late_attendance,
            "finish_attendance": finish_attendance,  # Add this line
            "Enter_work": enter_work,
            "Leave_work": leave_work
        }
        ref.child(user_id).set(new_user_data)

        # Capture and save face image
        self.capture_and_confirm_image(user_id)
        self.update_user_list()  # Refresh user list
        self.fetch_firebase_usage()

    def detect_and_save_face(self, user_id):
        # Path in Firebase Storage
        storage_path = f'{user_id}.png'
        
        cap = cv2.VideoCapture(0)

        # Capture a single frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture an image")
            cap.release()
            return

        # Convert the frame for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Detect faces in the frame
        detection_result = detector.detect(image)

        if detection_result.detections:
            # Save the cropped face locally temporarily
            cropped_face = self.visualize_and_crop(frame, detection_result)
            temp_image_path = f'temp_{user_id}.png'
            cv2.imwrite(temp_image_path, cropped_face)
            
            # Upload the image to Firebase Storage
            bucket = storage.bucket()
            blob = bucket.blob(storage_path)
            blob.upload_from_filename(temp_image_path)

            # Clean up the temporary local file
            os.remove(temp_image_path)
            print(f"Uploaded face image for {user_id} to Firebase Storage")
        else:
            print("No face detected")

        cap.release()
        cv2.destroyAllWindows()

    def visualize_and_crop(self, image, detection_result):
        height, width, _ = image.shape

        # Find the largest detected face
        max_area = 0
        closest_detection = None
        for detection in detection_result.detections:
            bbox = detection.bounding_box
            area = bbox.width * bbox.height
            if area > max_area and detection.categories[0].score >= CONFIDENCE_THRESHOLD:
                max_area = area
                closest_detection = detection

        if closest_detection is None:
            return image

        # Process the closest face and crop
        bbox = closest_detection.bounding_box
        start_point = max(bbox.origin_x - 30, 0), max(bbox.origin_y - 70, 0)
        end_point = min(bbox.origin_x + bbox.width + 30, width), min(bbox.origin_y + bbox.height + 30, height)

        # Return cropped face
        crop_img = image[start_point[1]:end_point[1], start_point[0]:end_point[0]]
        return crop_img

    def capture_and_confirm_image(self, user_id):
        # Perform face detection and save the image
        self.detect_and_save_face(user_id)

        # Display the captured image in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Captured Image for User {user_id}")
        layout = QVBoxLayout(dialog)

        # Load the image from Firebase Storage
        temp_image_path = f'temp_{user_id}.png'
        self.download_image_from_storage(user_id, temp_image_path)
        pixmap = QPixmap(temp_image_path)

        # Create a QLabel to show the image
        image_label = QLabel(dialog)
        image_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(image_label)

        # Create buttons for retrying the image capture and confirming
        retry_button = QPushButton("Retry Capture", dialog)
        confirm_button = QPushButton("Confirm", dialog)
        button_layout = QHBoxLayout()
        button_layout.addWidget(retry_button)
        button_layout.addWidget(confirm_button)
        layout.addLayout(button_layout)

        # Define the actions for the buttons
        retry_button.clicked.connect(lambda: self.retry_capture(user_id, image_label))
        confirm_button.clicked.connect(dialog.accept)

        dialog.exec()

        # Clean up the temporary local file
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

    def download_image_from_storage(self, user_id, local_path):
        # Download the image from Firebase Storage
        storage_path = f'{user_id}.png'
        bucket = storage.bucket()
        blob = bucket.blob(storage_path)

        try:
            # Download to the specified local path
            blob.download_to_filename(local_path)
            print(f"Downloaded {user_id}.png from Firebase Storage to {local_path}")
        except Exception as e:
            print(f"Failed to download image for user {user_id}: {str(e)}")
            raise

    def retry_capture(self, user_id, image_label):
        # Retry capturing and saving the face image
        self.detect_and_save_face(user_id)

        # Update the image displayed in the QLabel
        temp_image_path = f'temp_{user_id}.png'
        self.download_image_from_storage(user_id, temp_image_path)
        pixmap = QPixmap(temp_image_path)
        image_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
    def update_user(self):
        # Get the selected row from the user table
        selected_row = self.user_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Update Error", "Please select a user to update.")
            return

        # Get the user ID from the selected row
        user_id_item = self.user_table.item(selected_row, 0)
        if not user_id_item:
            QMessageBox.warning(self, "Update Error", "Selected user ID is invalid.")
            return

        user_id = user_id_item.text()

        # Create a dialog with options: Change Name, Change Work Time, Update Image
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Update User Options")
        msg_box.setText(f"What would you like to update for user {user_id}?")

        # Add buttons for "Change Name," "Change Work Time," "Update Image," and "Cancel"
        name_btn = msg_box.addButton("Change Name", QMessageBox.ButtonRole.ActionRole)
        work_time_btn = msg_box.addButton("Change Work Time", QMessageBox.ButtonRole.ActionRole)
        image_btn = msg_box.addButton("Update Image", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg_box.addButton(QMessageBox.StandardButton.Cancel)

        # Show the dialog and wait for the user's selection
        msg_box.exec()

        # Check which button was clicked and call the appropriate function
        if msg_box.clickedButton() == name_btn:
            self.change_user_name(user_id)
        elif msg_box.clickedButton() == work_time_btn:
            self.change_user_work_time(user_id)
        elif msg_box.clickedButton() == image_btn:
            self.capture_and_confirm_image(user_id)  # Use capture_and_confirm_image function
        else:
            # Cancel button was pressed; do nothing
            return

    def change_user_name(self, user_id):
        # Get the current name from the Firebase data
        current_name = ref.child(user_id).get().get('human_name', '')

        # Prompt the user for the new name, showing the current name on the first line
        new_name, ok = QInputDialog.getText(
            self, 
            "Change User Name", 
            f"{current_name} : This is the original name.\nEnter new name for the user:"
        )

        # Check if the user clicked "Cancel"
        if not ok:
            return  # Do nothing if the user clicked "Cancel"

        # Validate the input
        if not new_name.strip():
            QMessageBox.warning(self, "Update Error", "User name cannot be empty.")
            return

        # Update the user's name in Firebase
        ref.child(user_id).update({"human_name": new_name.strip()})

        # Refresh the user list to show the updated name
        self.update_user_list()
        self.fetch_firebase_usage()
        QMessageBox.information(self, "Success", f"User {user_id}'s name has been updated to {new_name}.")

    def change_user_work_time(self, user_id):
        # Get the current work times from Firebase
        user_data = ref.child(user_id).get()
        current_enter_work = user_data.get('Enter_work', 8)  # Default to 8 if not set
        current_leave_work = user_data.get('Leave_work', 17)  # Default to 17 if not set

        # Prompt the user for new work times
        enter_work, ok1 = QInputDialog.getInt(
            self, 
            "Change Enter Work Time", 
            f"Current Enter Work Time: {current_enter_work}\nEnter new Enter Work Time (0-23):", 
            value=current_enter_work, minValue=0, maxValue=23
        )
        if not ok1:
            return  # User cancelled

        leave_work, ok2 = QInputDialog.getInt(
            self, 
            "Change Leave Work Time", 
            f"Current Leave Work Time: {current_leave_work}\nEnter new Leave Work Time (0-23):", 
            value=current_leave_work, minValue=0, maxValue=23
        )
        if not ok2:
            return  # User cancelled

        # Update the work times in Firebase
        ref.child(user_id).update({"Enter_work": enter_work, "Leave_work": leave_work})

        # Refresh the user list to show the updated work times
        self.update_user_list()
        self.fetch_firebase_usage()
        QMessageBox.information(self, "Success", f"User {user_id}'s work times have been updated successfully.")

    def delete_user(self):
        # Get the selected row from the user table
        selected_row = self.user_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Delete Error", "Please select a user to delete.")
            return

        # Get the user ID from the selected row
        user_id_item = self.user_table.item(selected_row, 0)
        if not user_id_item:
            QMessageBox.warning(self, "Delete Error", "Selected user ID is invalid.")
            return

        user_id = user_id_item.text()

        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to delete user {user_id}?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # Delete the user data from Firebase
        ref.child(user_id).delete()

        # Delete the user's image from Firebase Storage
        storage_path = f'{user_id}.png'
        bucket = storage.bucket()
        blob = bucket.blob(storage_path)
        if blob.exists():
            blob.delete()
            print(f"Deleted image for user {user_id} in Firebase Storage")
        else:
            print(f"No image found for user {user_id} in Firebase Storage")

        # Refresh the user list to remove the deleted user
        self.update_user_list()
        self.fetch_firebase_usage()
        QMessageBox.information(self, "Success", f"User {user_id} has been deleted successfully.")

    def delete_all_users(self):
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete All",
            "Are you sure you want to delete all users? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return  # If the user selects 'No', do nothing

        # Fetch all users from Firebase
        students = ref.get()
        if not students:
            QMessageBox.warning(self, "Delete Error", "No users found to delete.")
            return

        # Delete each user data in Firebase and their associated images from Firebase Storage
        for user_id in students.keys():
            ref.child(user_id).delete()

            # Delete the user's image file from Firebase Storage
            storage_path = f'{user_id}.png'
            bucket = storage.bucket()
            blob = bucket.blob(storage_path)
            if blob.exists():
                blob.delete()
                print(f"Deleted image for user {user_id} in Firebase Storage")
            else:
                print(f"No image found for user {user_id} in Firebase Storage")

        # Refresh the user list to remove all users
        self.update_user_list()
        self.fetch_firebase_usage()
        QMessageBox.information(self, "Success", "All users have been deleted successfully.")

    def reset_user(self):
        # Get the selected row from the user table
        selected_row = self.user_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Reset Error", "Please select a user to reset.")
            return

        # Get the user ID from the selected row
        user_id_item = self.user_table.item(selected_row, 0)
        if not user_id_item:
            QMessageBox.warning(self, "Reset Error", "Selected user ID is invalid.")
            return

        user_id = user_id_item.text()

        # Confirm reset
        reply = QMessageBox.question(self, "Confirm Reset", f"Are you sure you want to reset the user {user_id}?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # Reset the user's attendance data in Firebase
        ref.child(user_id).update({
            "human_total_attendance": 0,
            "human_last_attendance_time": "0001-01-01 01:01:01",
            "punctual_attendance": 0,
            "late_attendance": 0,
            "finish_attendance": 0  # Add this line
        })

        # Refresh the user list to show the updated values
        self.update_user_list()
        self.fetch_firebase_usage()
        QMessageBox.information(self, "Success", f"User {user_id} has been reset successfully.")

    def reset_all_users(self):
        # Confirm reset
        reply = QMessageBox.question(self, "Confirm Reset All", "Are you sure you want to reset all users?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # Fetch all users from Firebase
        students = ref.get()
        if not students:
            QMessageBox.warning(self, "Reset Error", "No users found to reset.")
            return

        # Reset the attendance data for each user
        for user_id in students.keys():
            ref.child(user_id).update({
                "human_total_attendance": 0,
                "human_last_attendance_time": "0001-01-01 01:01:01",
                "punctual_attendance": 0,
                "late_attendance": 0,
                "finish_attendance": 0  # Add this line
            })

        # Refresh the user list to show the updated values
        self.update_user_list()
        self.fetch_firebase_usage()
        QMessageBox.information(self, "Success", "All users have been reset successfully.")

    def view_image(self):
        # Get the selected row from the user table
        selected_row = self.user_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "View Image Error", "Please select a user to view the image.")
            return

        # Get the user ID from the selected row
        user_id_item = self.user_table.item(selected_row, 0)
        if not user_id_item:
            QMessageBox.warning(self, "View Image Error", "Selected user ID is invalid.")
            return

        user_id = user_id_item.text()

        # Download the image from Firebase Storage
        storage_path = f'{user_id}.png'
        bucket = storage.bucket()
        blob = bucket.blob(storage_path)
        temp_image_path = f'temp_{user_id}.png'

        try:
            # Download the image to a temporary location
            blob.download_to_filename(temp_image_path)
            pixmap = QPixmap(temp_image_path)

            # Check if the image is loaded correctly
            if pixmap.isNull():
                QMessageBox.warning(self, "View Image Error", f"Failed to load image for user {user_id}.")
                return

            # Create a dialog to show the image
            dialog = QDialog(self)
            dialog.setWindowTitle(f"View Image - {user_id}")
            dialog.setMinimumSize(400, 400)
            main_layout = QVBoxLayout(dialog)

            # Create a widget to center the image
            center_widget = QWidget(dialog)
            center_layout = QHBoxLayout(center_widget)

            # Create a QLabel to display the image
            label = QLabel(center_widget)
            label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            label.setAlignment(Qt.AlignCenter)

            # Add QLabel to the center layout
            center_layout.addWidget(label)
            center_layout.setAlignment(Qt.AlignCenter)  # Center the layout

            # Add the centered widget to the main layout
            main_layout.addWidget(center_widget)

            dialog.exec()

            # Clean up the temporary local file
            os.remove(temp_image_path)
        except Exception as e:
            QMessageBox.warning(self, "View Image Error", f"Failed to download image for user {user_id}: {str(e)}")

    def calculate_size(self, data):
        if isinstance(data, dict):
            return sum(self.calculate_size(v) for v in data.values())
        elif isinstance(data, list):
            return sum(self.calculate_size(item) for item in data)
        elif isinstance(data, str):
            return len(data.encode('utf-8'))
        elif isinstance(data, (int, float, bool)):
            return len(str(data).encode('utf-8'))
        elif data is None:
            return 0
        else:
            return 0
        
    def fetch_firebase_usage(self):
        try:
            db_ref = db.reference('/')
            data = db_ref.get()
            total_size_bytes = self.calculate_size(data)
            database_limit_bytes = 1 * 1024 * 1024 * 1024
            remaining_bytes = database_limit_bytes - total_size_bytes
            usage_percentage1 = (total_size_bytes / database_limit_bytes) * 100
            self.database_label.setText(f"Realtime Database\n{total_size_bytes/(1024*1024):.6f} MB used ( {usage_percentage1:.6f}% )\n{remaining_bytes/(1024*1024):.6f} MB remaining\n{database_limit_bytes/(1024*1024):.6f} MB total capacity")
            bucket = storage.bucket()
            blobs = list(bucket.list_blobs())
            storage_used_bytes = sum(blob.size for blob in blobs)
            storage_limit_bytes = 5 * 1024 * 1024 * 1024
            storage_remaining_bytes = storage_limit_bytes - storage_used_bytes
            usage_percentage2 = (storage_used_bytes / storage_limit_bytes) * 100
            self.storage_label.setText(f"Cloud Storage\n{storage_used_bytes/(1024*1024):.2f} MB used ( {usage_percentage2:.2f}% )\n{storage_remaining_bytes/(1024*1024):.2f} MB remaining\n{storage_limit_bytes/(1024*1024):.2f} MB total capacity")
        except Exception as e:
            self.database_label.setText(f"Error fetching Firebase Database usage: {str(e)}")
            self.storage_label.setText(f"Error fetching Firebase Storage usage: {str(e)}")

    def init_manage_sheet(self):
        layout = QVBoxLayout(self.page_manage_sheets)
        
        # Create a label
        self.label = QLabel("Select Google Sheets files to manage:")
        layout.addWidget(self.label)
        
        # Create a filter layout
        filter_layout = QHBoxLayout()
        self.date_picker = QDateEdit(self)
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("dd-MM-yyyy")
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self.on_date_changed)
        filter_layout.addWidget(self.date_picker)
        
        # Add buttons for filter options
        self.show_all_button = QPushButton("Show All")
        self.show_all_button.clicked.connect(self.show_all_sheets)
        filter_layout.addWidget(self.show_all_button)
        
        self.reset_select_button = QPushButton("Reset Selection")
        self.reset_select_button.clicked.connect(self.reset_selection)
        filter_layout.addWidget(self.reset_select_button)
        
        self.refresh_button = QPushButton("Refresh Sheets")
        self.refresh_button.clicked.connect(self.fetch_and_display_sheets)
        filter_layout.addWidget(self.refresh_button)
        
        layout.addLayout(filter_layout)
        
        # List widget for displaying sheet names
        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)
        
        # Create a table for displaying sheet data
        self.data_table = QTableWidget(self)
        layout.addWidget(self.data_table)
        
        # Add row1 layout with Load, Rename, and Upload buttons
        row1_layout = QHBoxLayout()
        self.load_button = QPushButton("Load Sheet Data", self)
        self.load_button.clicked.connect(self.load_sheet_data)
        self.rename_button = QPushButton("Rename Selected File", self)
        self.rename_button.clicked.connect(self.rename_selected_file)
        self.upload_button = QPushButton("Upload Sheet", self)
        self.upload_button.clicked.connect(self.upload_sheet)
        row1_layout.addWidget(self.load_button)
        row1_layout.addWidget(self.rename_button)
        row1_layout.addWidget(self.upload_button)
        layout.addLayout(row1_layout)
        
        # Add row2 layout with Merge, Download, and Delete buttons
        row2_layout = QHBoxLayout()
        self.merge_button = QPushButton("Merge Selected Sheets", self)
        self.merge_button.clicked.connect(self.merge_selected_sheets)
        self.download_button = QPushButton("Download Selected Sheets", self)
        self.download_button.clicked.connect(self.download_selected_sheets)
        self.delete_button = QPushButton("Delete Selected Sheets", self)
        self.delete_button.clicked.connect(self.delete_selected_sheets)
        row2_layout.addWidget(self.merge_button)
        row2_layout.addWidget(self.download_button)
        row2_layout.addWidget(self.delete_button)
        layout.addLayout(row2_layout)
        
        # Add row3 layout with Merge All, Download All, and Delete All buttons
        row3_layout = QHBoxLayout()
        self.merge_all_button = QPushButton("Merge All Sheets", self)
        self.merge_all_button.clicked.connect(self.merge_all_sheets)
        self.download_all_button = QPushButton("Download All Sheets", self)
        self.download_all_button.clicked.connect(self.download_all_sheets)
        self.delete_all_button = QPushButton("Delete All Sheets", self)
        self.delete_all_button.clicked.connect(self.delete_all_sheets)
        row3_layout.addWidget(self.merge_all_button)
        row3_layout.addWidget(self.download_all_button)
        row3_layout.addWidget(self.delete_all_button)
        layout.addLayout(row3_layout)
        
        # Add row4 layout with Summarize buttons
        row4_layout = QHBoxLayout()
        self.summary_button = QPushButton("Summarize Selected Sheets", self)
        self.summary_button.clicked.connect(self.summarize_selected_sheets)
        self.summary_all_button = QPushButton("Summarize All Sheets", self)
        self.summary_all_button.clicked.connect(self.summarize_all_sheets)
        row4_layout.addWidget(self.summary_button)
        row4_layout.addWidget(self.summary_all_button)
        layout.addLayout(row4_layout)

        # Space label for drive usage
        self.space_label = QLabel("Fetching Google Drive space usage...", self)
        layout.addWidget(self.space_label)
        
        # Authenticate and fetch sheets
        self.authenticate_google_drive()
        self.fetch_and_display_sheets()
        self.fetch_drive_space()

    def authenticate_google_drive(self):
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Refresh or get new credentials if needed
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials-sheets.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('drive', 'v3', credentials=self.creds)

    def fetch_and_display_sheets(self):
        try:
            # Preserve the current show_all state
            current_show_all_state = self.show_all if hasattr(self, 'show_all') else False

            self.sheets = ezsheets.listSpreadsheets()
            if not self.sheets:
                self.label.setText("No Google Sheets files found.")
            else:
                # Restore the show_all state
                self.show_all = current_show_all_state
                self.update_list_display()
            
            # Refresh the drive space information
            self.fetch_drive_space()  # Add this line to refresh the drive space
        except Exception as e:
            self.label.setText(f"Error fetching sheets: {str(e)}")
            
    def on_date_changed(self):
        self.show_all = False
        self.update_list_display()

    def update_list_display(self):
        self.list_widget.clear()
        selected_date = self.date_picker.date().toString("dd-MM-yyyy")  # Update the date format to match the new sheet naming convention
        for sheet_id, sheet_name in self.sheets.items():
            # Split the sheet name based on the new format: hh-mm_dd-mm-yyyy_name
            parts = sheet_name.split('_')
            if len(parts) >= 2:  # Ensure the sheet name has enough parts to contain the date
                sheet_date = parts[1]  # Extract the date part (dd-mm-yyyy)
                if self.show_all or sheet_date == selected_date:
                    item = QListWidgetItem(f"{sheet_name} (ID: {sheet_id})")
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    self.list_widget.addItem(item)

    def show_all_sheets(self):
        self.show_all = True
        self.update_list_display()

    def reset_selection(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def load_sheet_data(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a Google Sheet to load.")
            return

        sheet_info = selected_item.text()
        sheet_id = sheet_info.split("(ID: ")[1].strip(")")
        
        try:
            spreadsheet = ezsheets.Spreadsheet(sheet_id)
            sheet = spreadsheet[0]
            self.data_table.clear()
            self.data_table.setColumnCount(sheet.columnCount)
            self.data_table.setRowCount(sheet.rowCount)

            header_row = sheet.getRow(1)
            if header_row:
                self.data_table.setHorizontalHeaderLabels(header_row)

            for row_num in range(1, sheet.rowCount + 1):
                row_data = sheet.getRow(row_num)
                if any(row_data):  # Avoid empty rows
                    for col_num, cell_data in enumerate(row_data):
                        self.data_table.setItem(row_num - 1, col_num, QTableWidgetItem(cell_data))

            self.data_table.resizeColumnsToContents()
            QMessageBox.information(self, "Success", f"Sheet {sheet.title} loaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sheet data: {str(e)}")

    def merge_selected_sheets(self):
        selected_items = [item for item in self.list_widget.findItems("", Qt.MatchContains) if item.checkState() == Qt.Checked]
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one Google Sheet to merge.")
            return

        try:
            self.merge_sheets(selected_items)
            self.refresh_list_widget()
            QMessageBox.information(self, "Success", "Selected sheets merged successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to merge sheets: {str(e)}")

    def merge_all_sheets(self):
        all_items = [item for item in self.list_widget.findItems("", Qt.MatchContains)]
        if not all_items:
            QMessageBox.warning(self, "No Sheets", "No Google Sheets available to merge.")
            return

        try:
            self.merge_sheets(all_items)
            self.refresh_list_widget()
            QMessageBox.information(self, "Success", "All sheets merged successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to merge all sheets: {str(e)}")

    def merge_sheets(self, items):
        # Add "Finish attendance" to the header
        merged_data = [["Name", "Attendance time", "Punctual attendance", "Late attendance", "Finish attendance"]]
        for item in items:
            sheet_info = item.text()
            sheet_id = sheet_info.split("(ID: ")[1].strip(")")
            spreadsheet = ezsheets.Spreadsheet(sheet_id)
            sheet = spreadsheet[0]

            for row_num in range(2, sheet.rowCount + 1):  # Skip header row
                row_data = sheet.getRow(row_num)
                if any(row_data):
                    # Ensure there are enough columns for finish attendance, else add an empty string
                    if len(row_data) < 5:
                        row_data.append("")  # Add an empty value for finish attendance if missing
                    merged_data.append(row_data)

        from datetime import datetime
        # Sort the merged data based on the "Attendance time" column
        merged_data[1:] = sorted(merged_data[1:], key=lambda x: datetime.strptime(x[1], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        # Update the filename date format
        current_time = datetime.now().strftime("%H-%M_%d-%m-%Y")
        filename = f"{current_time}_Merged_and_Sorted_Sheet"
        merged_spreadsheet = ezsheets.createSpreadsheet(filename)
        merged_sheet = merged_spreadsheet[0]
        
        for row_num, row_data in enumerate(merged_data, start=1):
            merged_sheet.updateRow(row_num, row_data)

    def refresh_list_widget(self):
        self.fetch_and_display_sheets()  # Re-fetch and update the sheet list display

    def summarize_selected_sheets(self):
        selected_items = [item for item in self.list_widget.findItems("", Qt.MatchContains) if item.checkState() == Qt.Checked]
        self.summarize_sheets(selected_items)

    def summarize_all_sheets(self):
        all_items = [item for item in self.list_widget.findItems("", Qt.MatchContains)]
        self.summarize_sheets(all_items)

    def summarize_sheets(self, items):
        try:
            if not items:
                QMessageBox.warning(self, "No Selection", "No Google Sheets available to summarize.")
                return

            summary_data = defaultdict(lambda: {"Punctual": 0, "Late": 0, "Finish": 0, "Total": 0})
            name_filter = self.name_filter.text().strip().lower() if hasattr(self, 'name_filter') else ""

            for item in items:
                sheet_info = item.text()
                sheet_id = sheet_info.split("(ID: ")[1].strip(")")
                spreadsheet = ezsheets.Spreadsheet(sheet_id)
                sheet = spreadsheet[0]

                for row_num in range(2, sheet.rowCount + 1):
                    row_data = sheet.getRow(row_num)
                    if not any(row_data):
                        continue
                    name = row_data[0].strip().lower()
                    if name_filter and name_filter not in name:
                        continue

                    try:
                        punctual = int(row_data[2])
                        late = int(row_data[3])
                        finish = int(row_data[4])
                    except (IndexError, ValueError):
                        continue  # Skip rows that don't have the required numeric values

                    summary_data[name]["Punctual"] += punctual
                    summary_data[name]["Late"] += late
                    summary_data[name]["Finish"] += finish
                    summary_data[name]["Total"] += (punctual + late + finish)

            # Sorting based on user criteria
            sort_key = self.sorting_criteria.currentText() if hasattr(self, 'sorting_criteria') else "Total"
            reverse = self.sorting_order.currentText() == "Descending" if hasattr(self, 'sorting_order') else True
            sorted_summary = sorted(summary_data.items(), key=lambda x: x[1][sort_key.split()[0]], reverse=reverse)

            # Updating the data table
            self.data_table.clear()
            self.data_table.setColumnCount(5)
            self.data_table.setHorizontalHeaderLabels(["Name", "Punctual attendance", "Late attendance", "Finish attendance", "Total attendance"])
            self.data_table.setRowCount(len(sorted_summary))

            for row, (name, data) in enumerate(sorted_summary):
                self.data_table.setItem(row, 0, QTableWidgetItem(name))
                self.data_table.setItem(row, 1, QTableWidgetItem(str(data["Punctual"])))
                self.data_table.setItem(row, 2, QTableWidgetItem(str(data["Late"])))
                self.data_table.setItem(row, 3, QTableWidgetItem(str(data["Finish"])))
                self.data_table.setItem(row, 4, QTableWidgetItem(str(data["Total"])))

            self.data_table.resizeColumnsToContents()
            QMessageBox.information(self, "Success", "Summary generated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate summary: {str(e)}")

    def rename_selected_file(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a Google Sheet to rename.")
            return

        sheet_info = selected_item.text()
        sheet_id = sheet_info.split("(ID: ")[1].strip(")")
        original_name = sheet_info.split(" (ID: ")[0]

        # Split the name at the second underscore
        parts = original_name.split('_', 2)
        if len(parts) < 3:
            QMessageBox.warning(self, "Invalid Format", "The sheet name format is not as expected.")
            return

        # Prompt the user to edit only the part after the second underscore
        new_suffix, ok = QInputDialog.getText(self, 'Rename File', f'Current suffix: {parts[2]}\nEnter new suffix:')
        if ok and new_suffix.strip():
            try:
                # Combine the original parts with the new suffix to form the new name
                new_name = f"{parts[0]}_{parts[1]}_{new_suffix.strip()}"
                file_metadata = {'name': new_name}
                self.service.files().update(fileId=sheet_id, body=file_metadata, supportsAllDrives=True).execute()
                QMessageBox.information(self, "Success", f"File renamed to {new_name}.")
                self.fetch_and_display_sheets()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename file: {str(e)}")
        else:
            QMessageBox.warning(self, "Invalid Input", "The new suffix cannot be empty.")

    def upload_sheet(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File to Upload", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        
        if not file_path:
            QMessageBox.warning(self, "No File Selected", "Please select a file to upload.")
            return

        try:
            file_metadata = {
                'name': os.path.basename(file_path).replace('.xlsx', ''),
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
            media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            QMessageBox.information(self, "Success", f"File uploaded successfully with ID: {file.get('id')}")
            self.fetch_and_display_sheets()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload file: {str(e)}")

    def download_selected_sheets(self):
        selected_items = [item for item in self.list_widget.findItems("", Qt.MatchContains) if item.checkState() == Qt.Checked]
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one Google Sheet to download.")
            return
        self.download_sheets(selected_items)

    def download_all_sheets(self):
        all_items = [item for item in self.list_widget.findItems("", Qt.MatchContains)]
        if not all_items:
            QMessageBox.warning(self, "No Sheets", "No Google Sheets available to download.")
            return
        self.download_sheets(all_items)

    def download_sheets(self, items):
        download_path = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if not download_path:
            QMessageBox.warning(self, "No Directory Selected", "Please select a directory to save the downloaded sheets.")
            return

        try:
            for item in items:
                sheet_info = item.text()
                sheet_id = sheet_info.split("(ID: ")[1].strip(")")
                spreadsheet = ezsheets.Spreadsheet(sheet_id)
                spreadsheet.downloadAsExcel(os.path.join(download_path, f"{spreadsheet.title}.xlsx"))
            QMessageBox.information(self, "Success", "Selected sheets downloaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download sheets: {str(e)}")

    def delete_selected_sheets(self):
        selected_items = [item for item in self.list_widget.findItems("", Qt.MatchContains) if item.checkState() == Qt.Checked]
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one Google Sheet to delete.")
            return

        confirm = QMessageBox.question(self, 'Delete Sheets', "Are you sure you want to delete the selected sheets?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.delete_sheets(selected_items)

    def delete_all_sheets(self):
        password, ok = QInputDialog.getText(self, 'Delete All Sheets', 'Enter password:', QLineEdit.EchoMode.Password)
        if not (ok and password == '999'):
            QMessageBox.warning(self, 'Error', 'Incorrect Password')
            return

        all_items = [item for item in self.list_widget.findItems("", Qt.MatchContains)]
        if not all_items:
            QMessageBox.warning(self, "No Sheets", "No Google Sheets available to delete.")
            return

        confirm = QMessageBox.question(self, 'Delete All Sheets', "Are you sure you want to delete all sheets?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.delete_sheets(all_items)

    def delete_sheets(self, items):
        try:
            for item in items:
                sheet_info = item.text()
                sheet_id = sheet_info.split("(ID: ")[1].strip(")")
                spreadsheet = ezsheets.Spreadsheet(sheet_id)
                spreadsheet.delete()
                self.permanently_delete_file(sheet_id)
            QMessageBox.information(self, "Success", "Selected sheets deleted permanently.")
            self.refresh_list_widget()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete sheets: {str(e)}")

    def permanently_delete_file(self, file_id):
        try:
            self.service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        except Exception as e:
            print(f"Error deleting file from trash: {str(e)}")

    def fetch_drive_space(self):
        try:
            about_info = self.service.about().get(fields="storageQuota").execute()
            limit = int(about_info['storageQuota']['limit'])
            usage = int(about_info['storageQuota']['usage'])
            remaining = limit - usage
            usage_percentage = (usage / limit) * 100

            # Convert values to both GB and MB
            usage_gb = usage / (1024**3)
            remaining_gb = remaining / (1024**3)
            limit_gb = limit / (1024**3)
            usage_mb = usage / (1024**2)
            remaining_mb = remaining / (1024**2)
            limit_mb = limit / (1024**2)

            # Update the label text with both GB and MB values
            self.space_label.setText(
                f"Google Drive Space :\n"
                f"{usage_gb:.2f} GB / {usage_mb:.2f} MB used ({usage_percentage:.2f}%)\n"
                f"{remaining_gb:.2f} GB / {remaining_mb:.2f} MB remaining\n"
                f"{limit_gb:.2f} GB / {limit_mb:.2f} MB total capacity"
            )
        except Exception as e:
            self.space_label.setText(f"Error fetching drive space: {str(e)}")

    def init_settings_page(self):
        layout = QVBoxLayout(self.page_setting)

        # Center the layout vertically
        layout.setAlignment(Qt.AlignTop)

        # Add a label with details above the Factory Reset button
        self.details_label = QLabel("This action will permanently delete all data in Firebase and local tokens.\n"
                                    "Please proceed with caution as this cannot be undone.")
        self.details_label.setWordWrap(True)  # Enable word wrapping for multi-line text
        layout.addWidget(self.details_label, alignment=Qt.AlignCenter)

        # Add Factory Reset button
        self.factory_reset_button = QPushButton("Factory Reset")
        self.factory_reset_button.setToolTip("This will delete all data in Firebase and local tokens.")
        self.factory_reset_button.setFixedSize(200, 50)  # Set the desired width and height in pixels

        layout.addWidget(self.factory_reset_button, alignment=Qt.AlignCenter)

        # Connect the Factory Reset button to the reset function
        self.factory_reset_button.clicked.connect(self.factory_reset)

    def factory_reset(self):
        # Confirm the factory reset action
        reply = QMessageBox.question(
            self,
            "Confirm Factory Reset",
            "Are you sure you want to reset all settings and delete all data?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return  # User canceled the action

        # Prompt for password
        password, ok = QInputDialog.getText(self, 'Password Required', 'Enter password:', QLineEdit.EchoMode.Password)
        
        # Check if the password was entered and is correct
        if not ok or password != 'XXX':  # Replace 'your_password_here' with the actual password
            QMessageBox.warning(self, 'Incorrect Password', 'The password you entered is incorrect.')
            return  # Exit the function if the password is incorrect

        # Proceed with the factory reset if the password is correct
        try:
            # Delete all data in Firebase Realtime Database
            db.reference('/').delete()

            # Delete all files in Firebase Storage
            bucket = storage.bucket()
            blobs = list(bucket.list_blobs())
            for blob in blobs:
                blob.delete()

            # Delete local files
            local_files = ['token.json', 'token-sheets.pickle', 'token-drive.pickle']
            for file_name in local_files:
                if os.path.exists(file_name):
                    os.remove(file_name)
                    print(f"Deleted {file_name}")
                else:
                    print(f"{file_name} does not exist.")

            QMessageBox.information(self, "Factory Reset", "All data and settings have been successfully reset.")
            self.update_user_list()  # Refresh the user list in case it is still visible
            self.fetch_firebase_usage()  # Refresh usage details after reset

        except Exception as e:
            QMessageBox.critical(self, "Factory Reset Failed", f"An error occurred during the reset process: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Load style file
    with open("style.qss") as f:
        style_str = f.read()

    app.setStyleSheet(style_str)
  
    window = MainWindow()
    window.show()

    sys.exit(app.exec())