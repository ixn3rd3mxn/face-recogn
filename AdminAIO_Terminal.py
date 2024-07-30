import cv2
import os
import pickle
import numpy as np
import face_recognition
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import time

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

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
    if students:
        print("Current students in the database:")
        for student_id, student_data in students.items():
            print(f"ID: {student_id}, Name: {student_data['name']}, "
                  f"Total Attendance: {student_data['total_attendance']}, "
                  f"Last Attendance Time: {student_data['last_attendance_time']}")
    else:
        print("No students found in the database.")

def add_student():
    student_id = input("Enter student ID: ")
    name = input("Enter student name: ")

    student_data = {
        "name": name,
        "total_attendance": total_attendance,
        "last_attendance_time": last_attendance_time
    }

    ref.child(student_id).set(student_data)
    print(f"Student {name} with ID {student_id} added to the database.")

    detect_and_save_faces(student_id)

def delete_student():
    student_id = input("Enter the student ID to delete: ")
    if ref.child(student_id).get():
        ref.child(student_id).delete()
        print(f"Student with ID {student_id} has been deleted from the database.")

        # Delete student's folder from Firebase Storage
        bucket = storage.bucket()
        blobs = bucket.list_blobs(prefix=f'Images/{student_id}/')
        for blob in blobs:
            blob.delete()
            print(f"Deleted {blob.name} from Firebase Storage.")

        # Delete student's folder from local machine
        local_folder_path = os.path.join('Images', student_id)
        if os.path.exists(local_folder_path):
            for filename in os.listdir(local_folder_path):
                file_path = os.path.join(local_folder_path, filename)
                os.remove(file_path)
            os.rmdir(local_folder_path)
            print(f"Deleted folder {local_folder_path} from local machine.")
    else:
        print(f"No student found with ID {student_id}.")

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
    print("Waiting for the camera to stabilize...")
    time.sleep(5)
    print("Camera is ready. Starting face detection.")

    count = 0  # Counter for the saved cropped faces
    max_images = 30  # Maximum number of images to save

    while count < max_images:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
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
            print(f'Uploaded {file_name} to Firebase Storage')

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

    print("Encoding Complete and File Saved")

def find_encodings(images_list):
    encode_list = []
    for img in images_list:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)
        if encodings:
            encode = encodings[0]
            encode_list.append(encode)
    return encode_list

def delete_all_data():
    # Delete all students from the Realtime Database
    ref.delete()
    print("All student data has been deleted from the Realtime Database.")

    # Delete all images from Firebase Storage
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix='Images/')
    for blob in blobs:
        blob.delete()
        print(f"Deleted {blob.name} from Firebase Storage.")

    # Delete all images from the local machine
    local_folder_path = 'Images'
    if os.path.exists(local_folder_path):
        for root, dirs, files in os.walk(local_folder_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(local_folder_path)
        print(f"Deleted all images from local folder {local_folder_path}.")

    # Delete EncodeFile.p from the local machine
    encode_file_path = 'EncodeFile.p'
    if os.path.exists(encode_file_path):
        os.remove(encode_file_path)
        print("Deleted EncodeFile.p from the local machine.")

def main():
    while True:
        print("\nMenu:")
        print("1. Show available folders and display all students")
        print("2. Add a student and detect faces")
        print("3. Delete a student")
        print("4. Encode all images")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            bucket_name = "faceplus-1b3e4.appspot.com"
            folders = list_subfolders_in_images(bucket_name)
            print("Existing folders in 'Images' folder in Firebase Storage:")
            for folder in folders:
                print(folder)
            display_students()
        elif choice == '2':
            add_student()
        elif choice == '3':
            delete_student()
        elif choice == '4':
            encode_all_images()
        elif choice == '5':
            break
        elif choice == '999':  # Secret menu option
            confirm = input("Are you sure you want to delete all data? This action cannot be undone. (yes/no): ")
            if confirm.lower() == 'yes':
                delete_all_data()
            else:
                print("Deletion canceled.")
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
