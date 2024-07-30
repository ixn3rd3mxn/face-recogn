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

from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QLabel, QLineEdit, QTextEdit, QMessageBox, QInputDialog)

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


def list_subfolders_in_images(bucket_name):
    bucket = storage.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix='Images/')

    folders = set()
    for blob in blobs:
        parts = blob.name.split('/')
        if len(parts) > 2:  # Make sure it is a subfolder
            folders.add(parts[1])

    return folders


def display_students():
    students = ref.get()
    student_list = ""
    if students:
        student_list += "Current students in the database:\n"
        for student_id, student_data in students.items():
            student_list += (f"ID: {student_id}, Name: {student_data['name']}, "
                             f"Total Attendance: {student_data['total_attendance']}, "
                             f"Last Attendance Time: {student_data['last_attendance_time']}\n")
    else:
        student_list = "No students found in the database."
    return student_list


def add_student(student_id, name):
    student_data = {
        "name": name,
        "total_attendance": total_attendance,
        "last_attendance_time": last_attendance_time
    }

    ref.child(student_id).set(student_data)
    detect_and_save_faces(student_id)


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


def visualize(image, detection_result, confidence_threshold: float, frame_counter: int, folder_name: str) -> np.ndarray:
    annotated_image = image.copy()
    height, width, _ = image.shape
    for detection in detection_result.detections:
        # Only visualize detections with a confidence score above the threshold
        if detection.categories[0].score < confidence_threshold:
            continue

        bbox = detection.bounding_box
        start_point = max(bbox.origin_x - 30, 0), max(bbox.origin_y - 70, 0)
        end_point = min(bbox.origin_x + bbox.width + 30, width), min(bbox.origin_y + bbox.height + 30, height)
        cv2.rectangle(annotated_image, start_point, end_point, (255, 0, 0), 3)

        # Crop face and save it with margin
        crop_img = image[start_point[1]:end_point[1], start_point[0]:end_point[0]]
        face_filename = os.path.join('Images', folder_name, f'{folder_name}_{frame_counter}.png')
        cv2.imwrite(face_filename, crop_img)

        category = detection.categories[0]
        category_name = category.category_name
        category_name = '' if category_name is None else category_name
        probability = round(category.score, 2)
        result_text = f"{category_name} ({probability})"
        text_location = (10 + bbox.origin_x, 10 + 10 + bbox.origin_y)
        cv2.putText(annotated_image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
    return annotated_image


def detect_and_save_faces(folder_name):
    output_dir = os.path.join('Images', folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cap = cv2.VideoCapture(0)

    # Wait for the camera to stabilize
    time.sleep(5)

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


def upload_new_images(student_id):
    folder_path = os.path.join('Images', student_id)

    if os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
            img_path = os.path.join(folder_path, filename)
            file_name = f'Images/{student_id}/{filename}'
            bucket = storage.bucket()
            blob = bucket.blob(file_name)
            blob.upload_from_filename(img_path)


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


class FaceRecognitionApp(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Face Recognition Management')

        self.layout = QVBoxLayout()

        self.display_folders_btn = QPushButton('Show Available Folders')
        self.display_folders_btn.clicked.connect(self.show_folders)
        self.layout.addWidget(self.display_folders_btn)

        self.display_students_btn = QPushButton('Display All Students')
        self.display_students_btn.clicked.connect(self.show_students)
        self.layout.addWidget(self.display_students_btn)

        self.add_student_btn = QPushButton('Add Student')
        self.add_student_btn.clicked.connect(self.add_student)
        self.layout.addWidget(self.add_student_btn)

        self.delete_student_btn = QPushButton('Delete Student')
        self.delete_student_btn.clicked.connect(self.delete_student)
        self.layout.addWidget(self.delete_student_btn)

        self.encode_images_btn = QPushButton('Encode All Images')
        self.encode_images_btn.clicked.connect(self.encode_images)
        self.layout.addWidget(self.encode_images_btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

        self.setLayout(self.layout)

    def show_folders(self):
        bucket_name = "faceplus-1b3e4.appspot.com"
        folders = list_subfolders_in_images(bucket_name)
        folders_text = "Existing folders in 'Images' folder in Firebase Storage:\n"
        folders_text += "\n".join(folders)
        self.output.setText(folders_text)

    def show_students(self):
        students_text = display_students()
        self.output.setText(students_text)

    def add_student(self):
        student_id, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter student ID:')
        if ok and student_id:
            name, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter student name:')
            if ok and name:
                add_student(student_id, name)
                QMessageBox.information(self, 'Info', f'Student {name} with ID {student_id} added.')
                self.output.append(f"Started detecting and saving faces for {name} (ID: {student_id}).")
                self.detect_and_save_faces(student_id)

    def delete_student(self):
        student_id, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter student ID to delete:')
        if ok and student_id:
            if delete_student(student_id):
                QMessageBox.information(self, 'Info', f'Student with ID {student_id} has been deleted.')
            else:
                QMessageBox.warning(self, 'Warning', f'No student found with ID {student_id}.')

    def encode_images(self):
        encode_all_images()
        QMessageBox.information(self, 'Info', 'Encoding Complete and File Saved')

    def detect_and_save_faces(self, student_id):
        detect_and_save_faces(student_id)
        self.output.append(f"Completed detecting and saving faces for student ID: {student_id}.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FaceRecognitionApp()
    ex.show()
    sys.exit(app.exec())
