import sys
import cv2
import os
import pickle
import numpy as np
import face_recognition
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

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceplus-1b3e4-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "faceplus-1b3e4.appspot.com"
})

# Create a FaceDetector object
CONFIDENCE_THRESHOLD = 0.7
base_options = python.BaseOptions(model_asset_path='detector.tflite')
options = vision.FaceDetectorOptions(base_options=base_options, min_detection_confidence=CONFIDENCE_THRESHOLD)
detector = vision.FaceDetector.create_from_options(options)

# Reference to the Firebase Realtime Database
ref = db.reference('Students')

# Constant values for total_attendance and last_attendance_time
total_attendance = 0
last_attendance_time = "0001-01-01 01:01:01"

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(875, 665)
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
            {"name": "  Manage Users", "icon": "./icon/ListUser.ico"},
            {"name": "  Encode Images", "icon": "./icon/EncodeImage.ico"},
            {"name": "  Reset All", "icon": "./icon/ResetAll.ico"},
        ]

        # Initialize the UI elements and slots
        self.init_list_widget()
        self.init_stackwidget()
        self.init_single_slot()

        # Set up the additional UI pages
        self.init_manage_users()
        self.init_encode_images()
        self.init_reset_all()
        self.update_user_list()

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
        self.page_encode_images = QWidget()
        self.page_reset_all = QWidget()

        # Add custom pages to the stack widget
        self.main_content.addWidget(self.page_manage_users)
        self.main_content.addWidget(self.page_encode_images)
        self.main_content.addWidget(self.page_reset_all)

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

    def init_manage_users(self):
        layout = QVBoxLayout(self.page_manage_users)

        # Create the table widget with 6 columns
        self.user_table = QTableWidget(0, 6)  # Adjusted to 6 columns
        self.user_table.setHorizontalHeaderLabels(["ID", "Name", "Punctual Attendance", "Late Attendance", "Total Attendance", "Last Attendance Time"])
        
        # Adjust column widths for proper space allocation
        self.user_table.setColumnWidth(0, 1)  # ID column
        self.user_table.setColumnWidth(1, 130)  # Name column
        self.user_table.setColumnWidth(2, 130)  # Punctual Attendance column
        self.user_table.setColumnWidth(3, 100)  # Late Attendance column
        self.user_table.setColumnWidth(4, 100)  # Total Attendance column
        self.user_table.setColumnWidth(5, 110)  # Last Attendance Time column

        self.user_table.horizontalHeader().setStretchLastSection(True)  # Stretch the last column to fill available space
        
        layout.addWidget(self.user_table)

        # Output text area for displaying messages, placed below the user list
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # Buttons for managing users
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add User")
        add_btn.clicked.connect(self.add_user)
        btn_layout.addWidget(add_btn)

        delete_btn = QPushButton("Delete User")
        delete_btn.clicked.connect(self.delete_user)
        btn_layout.addWidget(delete_btn)

        view_images_btn = QPushButton("View Images")
        view_images_btn.clicked.connect(self.view_images)
        btn_layout.addWidget(view_images_btn)

        edit_btn = QPushButton("Edit User")
        edit_btn.clicked.connect(self.edit_user)
        btn_layout.addWidget(edit_btn)

        layout.addLayout(btn_layout)


    def update_user_list(self):
        # Clear the table before populating
        self.user_table.setRowCount(0)
        students = ref.get()
        if students:
            for student_id, student_data in students.items():
                row_position = self.user_table.rowCount()
                self.user_table.insertRow(row_position)

                # Create and add non-editable items to the table
                id_item = QTableWidgetItem(student_id)
                name_item = QTableWidgetItem(student_data.get('name', ''))
                punctual_attendance_item = QTableWidgetItem(str(student_data.get('punctual_attendance', 0)))
                late_attendance_item = QTableWidgetItem(str(student_data.get('late_attendance', 0)))
                attendance_item = QTableWidgetItem(str(student_data.get('total_attendance', 0)))
                time_item = QTableWidgetItem(student_data.get('last_attendance_time', ''))

                # Set flags to make them non-editable
                id_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                name_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                punctual_attendance_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                late_attendance_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                attendance_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                time_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

                # Add items to the table
                self.user_table.setItem(row_position, 0, id_item)
                self.user_table.setItem(row_position, 1, name_item)
                self.user_table.setItem(row_position, 2, punctual_attendance_item)
                self.user_table.setItem(row_position, 3, late_attendance_item)
                self.user_table.setItem(row_position, 4, attendance_item)
                self.user_table.setItem(row_position, 5, time_item)


    def init_encode_images(self):
        layout = QVBoxLayout(self.page_encode_images)

        self.encode_btn = QPushButton("Start Encoding")
        self.encode_btn.clicked.connect(self.start_encoding)
        layout.addWidget(self.encode_btn)

        self.timer_label = QLabel("Elapsed Time: 00:00:00")
        layout.addWidget(self.timer_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.elapsed_timer = QElapsedTimer()  # Use QElapsedTimer instead of QTime

    def start_encoding(self):
        self.elapsed_timer.start()  # Start the elapsed timer
        self.timer.start(1000)  # Update every second

        # Start encoding logic here
        self.encode_thread = EncodeThread()
        self.encode_thread.finished.connect(self.on_encoding_finished)
        self.encode_thread.start()

    def update_timer(self):
        elapsed_seconds = self.elapsed_timer.elapsed() // 1000  # Get elapsed time in seconds
        elapsed_time = time.strftime('%H:%M:%S', time.gmtime(elapsed_seconds))
        self.timer_label.setText(f"Elapsed Time: {elapsed_time}")

    def on_encoding_finished(self):
        self.timer.stop()
        total_time = self.elapsed_timer.elapsed() // 1000
        total_time_str = time.strftime('%H:%M:%S', time.gmtime(total_time))
        self.timer_label.setText(f"Encoding Complete. Duration: {total_time_str}")

    def init_reset_all(self):
        layout = QVBoxLayout(self.page_reset_all)

        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self.prompt_password)
        layout.addWidget(self.reset_btn)

    def prompt_password(self):
        password, ok = QInputDialog.getText(self, 'Reset All', 'Enter password:', QLineEdit.EchoMode.Password)
        if ok and password == '999':
            reset_all_data()
            self.update_user_list()  # Refresh the user list to clear old data
            self.output_append('All data has been reset.')
        else:
            QMessageBox.warning(self, 'Error', 'Incorrect Password')


    def output_append(self, text):
        self.output.append(text)

    def add_user(self):
        student_id, ok = QInputDialog.getText(self, 'Add User', 'Enter student ID:')
        if ok and student_id:
            name, ok = QInputDialog.getText(self, 'Add User', 'Enter student name:')
            if ok and name:
                # Detect and save faces for the new user
                self.output_append(f"Starting face capture for {name} (ID: {student_id})...")
                detect_and_save_faces(student_id)
                
                # Add the student to Firebase
                add_student(student_id, name)
                self.update_user_list()
                self.output_append(f"User {name} with ID {student_id} added successfully.")

    def delete_user(self):
        current_row = self.user_table.currentRow()
        if current_row >= 0:
            student_id = self.user_table.item(current_row, 0).text()  # Get the student ID from the selected row

            confirm = QMessageBox.question(self, 'Delete User',
                                        f"Are you sure you want to delete the user with ID {student_id}?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                if delete_student(student_id):
                    self.update_user_list()
                    self.output_append(f"User with ID {student_id} deleted successfully.")
                else:
                    self.output_append(f"No student found with ID {student_id}.")
        else:
            QMessageBox.warning(self, 'Error', 'Please select a user to delete.')

    def view_images(self):
        current_row = self.user_table.currentRow()
        if current_row >= 0:
            student_id = self.user_table.item(current_row, 0).text()  # Get the student ID from the selected row
            folder_path = os.path.join('Images', student_id)
            if os.path.isdir(folder_path):
                images = os.listdir(folder_path)
                total_size = 0
                image_count = len(images)
                image_details = f"Images for Student ID {student_id}:\n"
                image_details += f"Total images: {image_count}\n"
                for image in images:
                    image_path = os.path.join(folder_path, image)
                    file_size = os.path.getsize(image_path)
                    total_size += file_size
                    image_details += f"{image}: {file_size / 1024:.2f} KB\n"

                    # Load the image
                    img = cv2.imread(image_path)
                    if img is not None:
                        # Display the image using OpenCV
                        window_name = f"{student_id} - {image}"
                        cv2.imshow(window_name, img)
                        cv2.waitKey(0)  # Wait for a key press to move to the next image
                        cv2.destroyWindow(window_name)
                    else:
                        self.output_append(f"Failed to load image: {image_path}")

                image_details += f"Total size: {total_size / 1024:.2f} KB"
                self.output_append(image_details)
            else:
                self.output_append(f"No images found for student ID {student_id}.")
        else:
            QMessageBox.warning(self, 'Error', 'Please select a user to view images.')

    def edit_user(self):
        current_row = self.user_table.currentRow()
        if current_row >= 0:
            student_id = self.user_table.item(current_row, 0).text()
            name = self.user_table.item(current_row, 1).text()

            # Get new name value
            new_name, ok = QInputDialog.getText(self, 'Edit User', 'Edit name:', text=name)
            if ok and new_name:
                # Update the table
                self.user_table.setItem(current_row, 1, QTableWidgetItem(new_name))

                # Update Firebase
                ref.child(student_id).update({
                    'name': new_name
                })
                self.output_append(f"User {student_id} updated successfully.")
            else:
                self.output_append("Edit canceled or invalid name entered.")
        else:
            QMessageBox.warning(self, 'Error', 'Please select a user to edit.')


def add_student(student_id, name):
    # Initial data for a new student
    student_data = {
        "name": name,
        "total_attendance": total_attendance,
        "last_attendance_time": last_attendance_time,
        "late_attendance": 0,         # New field for late attendance
        "punctual_attendance": 0      # New field for punctual attendance
    }
    # Set the student's data in Firebase
    ref.child(student_id).set(student_data)


def detect_and_save_faces(folder_name):
    output_dir = os.path.join('Images', folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cap = cv2.VideoCapture(0)
    count = 0  # Counter for the saved cropped faces
    max_images = 30  # Maximum number of images to save

    while count < max_images:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to the format expected by MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Detect faces in the frame
        detection_result = detector.detect(image)

        # Visualize the detection results and save cropped faces
        annotated_image = visualize(frame, detection_result, CONFIDENCE_THRESHOLD, count, folder_name)

        # Display the annotated image
        cv2.imshow('Webcam Face Detection', annotated_image)

        # Exit loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        count += 1

    cap.release()
    cv2.destroyAllWindows()

    # Encode and upload images to Firebase Storage
    upload_new_images(folder_name)

def visualize(image, detection_result, confidence_threshold: float, frame_counter: int, folder_name: str) -> np.ndarray:
    annotated_image = image.copy()
    height, width, _ = image.shape

    if not detection_result.detections:
        return annotated_image

    # Find the closest face (largest bounding box area)
    max_area = 0
    closest_detection = None
    for detection in detection_result.detections:
        bbox = detection.bounding_box
        area = bbox.width * bbox.height
        if area > max_area and detection.categories[0].score >= confidence_threshold:
            max_area = area
            closest_detection = detection

    if closest_detection is None:
        return annotated_image

    # Process the closest face
    bbox = closest_detection.bounding_box
    start_point = max(bbox.origin_x - 30, 0), max(bbox.origin_y - 70, 0)
    end_point = min(bbox.origin_x + bbox.width + 30, width), min(bbox.origin_y + bbox.height + 30, height)
    cv2.rectangle(annotated_image, start_point, end_point, (255, 0, 0), 3)

    # Crop face and save it with margin
    crop_img = image[start_point[1]:end_point[1], start_point[0]:end_point[0]]
    face_filename = os.path.join('Images', folder_name, f'{folder_name}_{frame_counter}.png')
    cv2.imwrite(face_filename, crop_img)

    category = closest_detection.categories[0]
    category_name = category.category_name if category.category_name else ''
    probability = round(category.score, 2)
    result_text = f"{category_name} ({probability})"
    text_location = (10 + bbox.origin_x, 10 + 10 + bbox.origin_y)
    cv2.putText(annotated_image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)

    return annotated_image

def upload_new_images(student_id):
    folder_path = os.path.join('Images', student_id)
    if os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
            img_path = os.path.join(folder_path, filename)
            file_name = f'Images/{student_id}/{filename}'
            bucket = storage.bucket()
            blob = bucket.blob(file_name)
            blob.upload_from_filename(img_path)

def delete_student(student_id):
    if ref.child(student_id).get():
        ref.child(student_id).delete()
        # Delete student's folder from Firebase Storage
        bucket = storage.bucket()
        blobs = bucket.list_blobs(prefix=f'Images/{student_id}/')
        for blob in blobs:
            blob.delete()
        # Delete student's folder from local machine
        local_folder_path = os.path.join('Images', student_id)
        if os.path.exists(local_folder_path):
            for filename in os.listdir(local_folder_path):
                file_path = os.path.join(local_folder_path, filename)
                os.remove(file_path)
            os.rmdir(local_folder_path)
    else:
        return False
    return True

def reset_all_data():
    # Clear the Firebase database
    ref.set({})
    
    # Clear Firebase Storage
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix='Images/')
    for blob in blobs:
        blob.delete()
    
    # Clear local 'Images' folder
    local_folder_path = 'Images'
    if os.path.exists(local_folder_path):
        for folder_name in os.listdir(local_folder_path):
            folder_path = os.path.join(local_folder_path, folder_name)
            if os.path.isdir(folder_path):
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    os.remove(file_path)
                os.rmdir(folder_path)
    
    # Remove the encoding file
    if os.path.exists("EncodeFile.p"):
        os.remove("EncodeFile.p")

    # Clear the user table in the UI
    window.update_user_list()  # Ensure that the user list is updated in the UI


def encode_all_images():
    folder_path = 'Images'
    encode_dict = {}
    path_list = os.listdir(folder_path)
    for path in path_list:
        student_folder = os.path.join(folder_path, path)
        if os.path.isdir(student_folder):
            img_list = []
            for filename in os.listdir(student_folder):
                img_path = os.path.join(student_folder, filename)
                img = cv2.imread(img_path)
                if img is not None:
                    img_list.append(img)
            if img_list:
                encode_dict[path] = find_encodings(img_list)
    with open("EncodeFile.p", 'wb') as file:
        pickle.dump(encode_dict, file)

def find_encodings(images_list):
    encode_list = []
    for img in images_list:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)
        if encodings:
            encode = encodings[0]
            encode_list.append(encode)
    return encode_list

class EncodeThread(QThread):
    def run(self):
        encode_all_images()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Load style file
    with open("style.qss") as f:
        style_str = f.read()

    app.setStyleSheet(style_str)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
